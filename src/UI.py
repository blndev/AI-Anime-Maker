import os
import PIL
import gradio as gr
from hashlib import sha1
import time # for sleep in SKIP_AI
from datetime import datetime, timedelta
import logging

import src.config as config
import src.utils.fileIO as utils
import src.analytics as analytics
from src.genai import ConvertImage2ImageByStyle, ImageCaptioner
from src.SessionState import SessionState

# Set up module logger
logger = logging.getLogger(__name__)

if config.SKIP_ONNX or not config.is_feature_generation_with_token_enabled():
    def analyze_faces(pil_image: any):
        """ without onnx we cant detect and analyze faces"""
        return []
else:
    logger.info("Activating ONNX functions")
    from src.detectors.FaceAnalyzer import FaceAnalyzer
    _face_analyzer = None
    def analyze_faces(pil_image):
        global _face_analyzer
        if _face_analyzer == None: _face_analyzer = FaceAnalyzer()
        return _face_analyzer.get_gender_and_age_from_image(pil_image)

# used to get properties of the selected style liek prompt or strangth
# will be filled while interface is loading
style_details = {}

_AIHandler = ConvertImage2ImageByStyle(config.get_model(), max_size=config.get_max_size())
_ImageCaptioner = ImageCaptioner()

def action_session_initialized(request: gr.Request, session_state: SessionState):
    """Initialize analytics session when app loads.
    
    Args:
        request (gr.Request): The Gradio request object containing client information
        state_dict (dict): The current application state dictionary
    """
    logger.info("Session - %s - initialized with %i token for: %s",session_state.session, session_state.token, request.client.host)
    if config.is_analytics_enabled() and request:
        try:
            analytics.save_session(
                session=session_state.session, 
                ip=request.client.host,
                user_agent=request.headers["user-agent"], 
                languages=request.headers["accept-language"])
            logger.debug("Session - %s - saved for analytics",session_state.session)
        except Exception as e:
            logger.error("Error initializing analytics session: %s", str(e))
            logger.debug("Exception details:", exc_info=True)

def action_update_all_local_models():
    """updates the list of available models in the ui"""
    return gr.update(choices=utils.get_all_local_models(config.get_model_folder()))

session_image_hashes = {}
def action_handle_input_file(request: gr.Request, image: PIL.Image, gradio_state: str):
    """Analyze the Image, Handle Session Info, Save the input image in a cache if enabled, count token."""
    global session_image_hashes
    session_state = SessionState.from_gradio_state(gradio_state)
    # deactivate the start button on error
    if image is None: 
        return wrap_handle_input_response(session_state, False, "")
    # API Users don't have a request (by documentation)
    if not request: 
        return wrap_handle_input_response(session_state, False, "")

    input_file_path = ""
    image_sha1 = sha1(image.tobytes()).hexdigest()
    if config.is_input_cache_enabled():
        dir = config.get_output_folder()
        dir = os.path.join(dir, datetime.now().strftime("%Y%m%d"))
        input_file_path = utils.save_image_as_file(image, dir)

    logger.info(f"UPLOAD from {session_state.session} with ID: {image_sha1}")

    image_description = ""
    try:
        image_description = action_describe_image(image)
    except Exception as e:
        logger.error("Error creating image description: %s", str(e))
        #logger.debug("Exception details:", exc_info=True)
        gr.Warning("Could not create a proper image description. Please describe your image shortly for better results.")

    # variables used for analytics if enabled
    face_detected = False
    min_age = 0
    max_age = 0
    gender = 0
    new_token = 0 

    #analyzation of images will be done always
    #check that the image was not already used in this session
    analyze_input_image_details = True
    if config.is_feature_generation_with_token_enabled():
        min_age, max_age, gender, face_detected, analyze_input_image_details = check_same_upload_in_block_time(image_sha1)

    if analyze_input_image_details:
        detected_faces = []
        try:
            detected_faces = analyze_faces(image)
        except Exception as e:
            logger.error("Error while analyzing face: %s", str(e))
            logger.debug("Exception details:", exc_info=True)
        
        new_token = config.get_token_for_new_image()
        if len(detected_faces)>0:
            face_detected = True
            #we have minimum one face
            logger.debug("Bonus: face")
            face_bonus = config.get_token_bonus_for_face()
            if face_bonus>0: 
                new_token += face_bonus
                gr.Info(f"{face_bonus} Bonus token added for an Image with a Face!")

            # we have that bonus in a variable as we want to give it only once
            token_for_cuteness = config.get_token_bonus_for_cuteness()
            token_for_smiling = config.get_token_bonus_for_smile() 
            gender = 0 #{0: "unkown", 1: "male", 2: "female", 3: "female + male"}
            for face in detected_faces:
                #just save the jungest and oldest if we have multiple faces
                min_age = face["minAge"] if face["minAge"]<min_age or min_age == 0 else min_age
                max_age = face["maxAge"] if face["maxAge"]>max_age or max_age == 0 else max_age
                if face["isFemale"]: 
                    gender |= 2
                    # until we can recognize smiles we give bonus for other properties
                    if token_for_smiling>0:
                        logger.debug("Bonus: smiling")
                        new_token+=token_for_smiling
                        gr.Info(f"{token_for_smiling} special Bonus token added!")
                        token_for_smiling = 0 #apply only once per image
                elif face["isMale"]:
                    gender |= 1

                if token_for_cuteness>0 and (face["maxAge"]<20 or face["minAge"]>60):
                    logger.debug("Bonus: cuteness")
                    new_token+=token_for_cuteness
                    gr.Info(f"{token_for_cuteness} special Bonus token added!")
                    token_for_cuteness = 0 #allow bonus only once per upload

        # save the hash to prevent reuse
        session_image_hashes[image_sha1]={
            "dt": datetime.now()+timedelta(minutes=config.get_token_time_lock_for_new_image()),
            "gender": gender,
            "min_age": min_age,
            "max_age": max_age,
            "face_detected": face_detected
        }

    if config.is_feature_generation_with_token_enabled() and new_token>0:
        gr.Info(f"Total new Token: {new_token}")

    logger.info(f"UPLOAD ID {image_sha1} received {new_token} token total.")
    session_state.token += new_token

    if config.is_analytics_enabled():
        analytics.save_input_image_details(
            session=session_state.session, 
            sha1=image_sha1, 
            token=new_token,
            cache_path_and_filename=os.path.relpath(input_file_path, config.get_output_folder()), 
            face_detected=face_detected,
            min_age=min_age,
            max_age=max_age,
            gender=gender
            )    

    start_enabled = True if not config.is_feature_generation_with_token_enabled() else bool(session_state.token>0)
    return wrap_handle_input_response(session_state, start_enabled, image_description)

def check_same_upload_in_block_time(image_sha1):
    """check if the same file is uploaded from same user again to gain token"""
    analyzation_required = True
    face_detected = False
    min_age = 0
    max_age = 0
    gender = 0
    if image_sha1 in session_image_hashes.keys():
        # check if the image is locked
        last_upload = session_image_hashes[image_sha1]
        dt = last_upload["dt"]
        if dt>datetime.now():
            analyzation_required = False
            if config.is_feature_generation_with_token_enabled():
                gr.Warning(
                    f"""This image signature was already used to gain token.
                    New token for it will be provided after {dt.strftime("%d.%m.%Y - %H:%M")}""")
            gender=last_upload["gender"]
            min_age=last_upload["min_age"]
            max_age=last_upload["max_age"]
            face_detected=last_upload["face_detected"]
        else:
            #remove current entry as it is outdated
            del session_image_hashes[image_sha1]

    #cleanup the whole list of locked images to not waste memory
    try:
        keys_to_remove = [key for key, dt in session_image_hashes.items() if dt < datetime.now()]
        for key in keys_to_remove:
            del session_image_hashes[key]
        if len(keys_to_remove)>0:
            logger.info(f"Removed token lock for {len(keys_to_remove)} image(s)")
    except:
        pass
    return min_age, max_age, gender, face_detected, analyzation_required

def action_describe_image(image):
    """describe an image for better inpaint results."""
    if config.SKIP_AI: return "ai deactivated"
    # Fallback
    value = "please describe your image here"    
    try:
        value = _ImageCaptioner.describe_image(image)
        logger.debug("Image description: %s", value)
    except Exception:
        pass
    return value

def action_reload_model(model):
    if config.SKIP_AI: return
    logger.warning("Reloading model %s", model)
    try:
        _AIHandler.change_img2img_model(model=model)
        gr.Info(message=f"Model {model} loaded.", title="Model changed")
    except Exception as e:
        gr.Error(message=e.message)

def action_generate_image(request: gr.Request, image, style, strength, steps, image_description, gradio_state):
    """Convert the entire input image to the selected style."""
    global style_details
    session_state = SessionState.from_gradio_state(gradio_state)
    #setting token always to 10 if the feature is disabled saved a lot of "if feature enabled .." statements
    if session_state.token == None: session_state.token = 0 
    if not config.is_feature_generation_with_token_enabled(): session_state.token = 10

    try:
        if config.is_feature_generation_with_token_enabled() and session_state.token<=0:
            gr.Warning("You have not enough token to start a generation. Upload a new image for new token!")
            return wrap_generate_image_response(session_state, image)
        if image is None: 
            gr.Error("Start of Generation without image!")
            return wrap_generate_image_response(session_state, None)
        # API Users don't have a request object (by documentation)
        if request is None: 
            logger.warning("No request object. API usage?")
            return wrap_generate_image_response(session_state, None)

        logger.debug("Starting image generation")
        if image_description == None or image_description == "": image_description = _ImageCaptioner.describe_image(image)

        sd = style_details.get(style)
        if sd == None:
            sd = {
                "prompt": "",
                "negative_prompt": config.get_style_negative_prompt(99),#99 means you will get back the default overall negative prompt if style 99 does not exist
                "strength": config.get_default_strength(),
                "steps": config.get_default_steps()
            }
            # add to gloabel list for caching
            style_details[style] = sd

        prompt = f"{sd["prompt"]}: {image_description}"
        
        logger.info(f"GENERATE - {session_state.session} - {style}: {image_description}")

        # must be before resizing, otherwise hash will not be same as from source image
        # or adapt the source image saving with thumbnail property
        image_sha1 = sha1(image.tobytes()).hexdigest()

        # use always the sliders for strength and steps if they are enabled
        if not config.UI_show_strength_slider(): strength = sd["strength"]
        if not config.UI_show_steps_slider(): steps = sd["steps"]

        if config.SKIP_AI:
            result_image = utils.image_convert_to_sepia(image)
            time.sleep(5)
        else:
            # Generate new picture
            result_image = _AIHandler.generate_image(
                image = image,
                prompt=prompt, 
                negative_prompt=sd["negative_prompt"],
                steps=steps, 
                strength=strength,
                )
        
        # save generated file if enabled
        fn=None
        if config.is_save_output_enabled():
            folder_path=config.get_output_folder()
            folder_path = os.path.join(folder_path, datetime.now().strftime("%Y%m%d"))
            fn = utils.save_image_with_timestamp(
                image=result_image,
                folder_path=folder_path,
                reference=f"{image_sha1}-{style}",
                ignore_errors=True)

        if config.is_analytics_enabled():
            if config.is_save_output_enabled() and fn:
                rel_path = os.path.relpath(fn, config.get_output_folder())
            else:
                rel_path = None
            analytics.save_generation_details(
                session_state.session,
                sha1=image_sha1,
                style=style,
                prompt=image_description,
                output_filename=rel_path
                )
        session_state.token -= 1
        if session_state.token <= 0: gr.Warning("You running out of Token.\n\nUpload a new image to continue.")
        #make it smaller (WebP to JPG)
        result_image = result_image.convert("RGB") 
        return wrap_generate_image_response(session_state, result_image)
    except RuntimeError as e:
        logger.error("RuntimeError: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        gr.Error(e)
        return wrap_generate_image_response(session_state, None)

#--------------------------------------------------------------
# Gradio - Render UI
#--------------------------------------------------------------
def wrap_handle_input_response(session_state: SessionState, start_enabled: bool, image_description: str) -> list:
    """Create a consistent response format for handle_input_file action.
    
    Args:
        session_state: The current SessionState object
        start_enabled: Whether the start button should be enabled
        image_description: The generated image description
        
    Returns:
        List of values in the order: [start_button, text_description, local_storage, area_description, token_counter]
    """
    return [
        gr.update(interactive=start_enabled),
        image_description,
        session_state,
        gr.update(visible=True),
        session_state.token
    ]

def wrap_generate_image_response(session_state: SessionState, result_image: any) -> list:
    """Create a consistent response format for generate_image action.
    
    Args:
        session_state: The current SessionState object
        result_image: The generated image result
        
    Returns:
        List of values in the order: [output_image, local_storage, start_button, token_counter]
    """
    return [
        result_image,
        session_state,
        gr.update(interactive=bool(session_state.token>0)),
        session_state.token
    ]

def create_gradio_interface():
    global style_details
    with gr.Blocks(
        title=config.get_app_title(), 
        theme=config.UI_get_gradio_theme(),
        css="footer {visibility: hidden}",
        analytics_enabled=False
        ) as app:
        with gr.Row():
            gr.Markdown("### " + config.get_app_title()+"\n\n" + config.get_user_message())
            
        if config.DEBUG and not config.SKIP_AI:
            gr.Markdown("*DEBUG enabled*" + (" SKIP AI__" if config.SKIP_AI else ""))
            with gr.Row():
                with gr.Column():
                    model_dropdown = gr.Dropdown(choices=utils.get_all_local_models(config.get_model_folder()), value=config.get_model(), label="Models", allow_custom_value=True)
                with gr.Column():
                    refresh_model_list_button = gr.Button("refresh model list")
                    reload_button = gr.Button("load model")
                    reload_button.click(
                        fn=action_reload_model,
                        inputs=[model_dropdown],
                        outputs=[]
                    )
                    refresh_model_list_button.click(
                        fn=action_update_all_local_models,
                        inputs=[],
                        outputs=[model_dropdown]
                    )
        with gr.Row(visible=config.is_feature_generation_with_token_enabled()):
            with gr.Column():
                #token = gr.Session
                local_storage = gr.BrowserState() # do not initialize it with any value!!! this is used as default
                #token count is restored from app.load
                token_counter = gr.Number(visible=False, value=0)
                token_label = gr.Text(
                    show_label=False,
                    value=f"Current Token: 0",
                    info=config.get_token_explanation())
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(label="Input", type="pil", height=512)
                #describe_button = gr.Button("Describe your Image", interactive=False)
                with gr.Column(visible=False) as area_description:
                    text_description = gr.Textbox(label="change the image description for better results", show_label=True, max_length=90, submit_btn="↻")

                styles = []
                for i in range(1,config.get_style_count()+1):
                    name = config.get_style_name(i)
                    styles.append(name)
                    style_details[name] = {
                        "prompt": config.get_style_prompt(i),
                        "negative_prompt":config.get_style_negative_prompt(i),
                        "strength": config.get_style_strengths(i),
                        "steps": config.get_default_steps()
                    }
                if config.DEBUG: styles.append("Open Style")
                style_dropdown = gr.Radio(styles, label="Style", value=styles[0])
            with gr.Column():
                output_image = gr.Image(
                    label="Result", 
                    type="pil", 
                    height=512, 
                    show_download_button=True
                    )
                start_button = gr.Button("Start Creation", interactive=False, variant="primary")
                with gr.Column():
                    gr.Markdown(value="""
### Important Information

You can report any inappropriate image generation.

**Note:** If you click "report," we will save the settings for analysis.
As all communication is anonymous through. We can't send any feedback to you.
                                """)
                    flag_image_text = gr.Text(label="Feedback", placeholder="What is wrong?")
                    flag_image_button = gr.Button("Report by clicking here", interactive=False)

                strength_slider = gr.Slider(label="Strength", minimum=0.1, maximum=1, value=config.get_default_strength(), step=0.1,  visible=config.UI_show_strength_slider())
                steps_slider = gr.Slider(label="Steps", minimum=10, maximum=100, value=config.get_default_steps(), step=5, visible=config.UI_show_steps_slider())
        
        def helper_display_token(token):
            return f"Current Token: {token}"
        
        @app.load(inputs=[local_storage], outputs=[local_storage, token_counter])
        def load_from_local_storage(request: gr.Request, gradio_state):
            # Restore token from local storage
            session_state = SessionState.from_gradio_state(gradio_state)

            # Initialize session when app loads
            action_session_initialized(request=request, session_state=session_state)
            
            if config.is_feature_generation_with_token_enabled(): 
                logger.debug("Restoring token from local storage: %s", session_state.token)
                logger.debug("Session ID: %s", session_state.session)
            return session_state, session_state.token

        token_counter.change(
            inputs=[token_counter],
            outputs=[token_label],
            fn=helper_display_token
        )

        # Save input image immediately on change
        # adapt wrap_handle_input_response if you change output params
        image_input.change(
            fn=action_handle_input_file,
            inputs=[image_input, local_storage],
            outputs=[start_button, text_description, local_storage, area_description, token_counter], 
            concurrency_limit=None,
            concurrency_id="new_image"
        )

        text_description.submit(
            fn=action_describe_image,
            inputs=[image_input],
            outputs=[text_description],
            concurrency_limit=10,
            concurrency_id="describe"
        )

        # adapt wrap_generate_image_response if you change output parameters
        start_button.click(
            fn=action_generate_image,
            inputs=[image_input, style_dropdown, strength_slider, steps_slider, text_description, local_storage],
            outputs=[output_image, local_storage, start_button, token_counter],
            concurrency_limit=config.GenAI_get_execution_batch_size(),
            concurrency_id="gpu_queue",
            show_progress="minimal"
            #batch=False,
            #max_batch_size=config.GenAI_get_execution_batch_size(),
        )

        def action_image_reported(gradio_state, feedback):
            session_state = SessionState.from_gradio_state(gradio_state)
            gr.Info("Thank you for the report. We will try to fine tune our model to avoid such generations in the future.")
            #TODO: use output sha1 or db id (send it to client) to fill teh blocked column in database
            logger.error(f"REPORT: User {session_state.session} flagged the last generation. Feedback '{feedback}'")
            return gr.update(interactive=False), ""
            
        flag_image_button.click(
            fn=action_image_reported,
            inputs=[local_storage, flag_image_text],
            outputs=[flag_image_button, flag_image_text]
        )
        def action__activate_button():
            return gr.update(interactive=True)
        output_image.change(fn=action__activate_button, outputs=[flag_image_button])

        disclaimer = config.get_app_disclaimer()
        if disclaimer:
            js=f"""
            () => {{
                // Overlay erstellen
                const overlay = document.createElement('div');
                overlay.style.position = 'fixed';
                overlay.style.top = 0;
                overlay.style.left = 0;
                overlay.style.width = '100%';
                overlay.style.height = '100%';
                overlay.style.color = 'white';
                overlay.style.backgroundColor = 'rgba(10, 0, 0, 0.9)';
                overlay.style.display = 'flex';
                overlay.style.justifyContent = 'center';
                overlay.style.alignItems = 'center';
                overlay.style.zIndex = 1000;

                // Nachricht und Button hinzufügen
                overlay.innerHTML = `
                <div style="padding: 20px; border-radius: 20px; text-align: center; box-shadow: 0px 4px 10px rgba(0, 0, 255, 0.3);">
                    <p style="margin-bottom: 20px;">{disclaimer}</p>
                    <button id="accept-btn" style="padding: 10px 20px; border: none; background: #4caf50; color: white; border-radius: 5px; cursor: pointer;">Accept</button>
                </div>
                `;

                // Overlay zur Seite hinzufügen
                document.body.appendChild(overlay);

                // Button-Click-Event, um Overlay zu schließen
                document.getElementById('accept-btn').onclick = () => {{
                    document.body.removeChild(overlay);
                }};
            }}
            """

            app.load(
                fn=None,
                inputs=None,
                outputs=None,
                js=js
            )
        #end if disclaimer activated
        return app
