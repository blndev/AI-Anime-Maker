import os
import gradio as gr
from hashlib import sha1
import time # for sleep in SKIP_AI
from datetime import datetime, timedelta
import logging
import uuid
from dataclasses import dataclass
from typing import Optional

import src.config as config
import src.utils as utils
import src.analytics as analytics
import src.AI as AI

@dataclass
class AppState:
    """State object for storing application data in browser."""
    token: int = 0
    session: str = str(uuid.uuid4())  # Generate a new UUID4 for each instance

    def __str__(self) -> str:
        """String representation for logging."""
        return f"AppState(token={self.token}, session={self.session})"

    def to_dict(self) -> dict:
        """Convert AppState to dictionary for serialization."""
        return {
            'token': self.token,
            'session': self.session
        }

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> 'AppState':
        """Create AppState from dictionary after deserialization."""
        if not data:
            return cls()
        return cls(
            token=data.get('token', 0),
            session=data.get('session', str(uuid.uuid4()))
        )

# Set up module logger
logger = logging.getLogger(__name__)

if config.SKIP_ONNX or not config.is_feature_generation_with_token_enabled():
    def analyze_faces(pil_image: any):
        """ without onnx we cant detect and analyze faces"""
        return []
else:
    logger.info("Loading ONNX functions")
    from src.onnx_analyzer import FaceAnalyzer
    fai = FaceAnalyzer() # singleton
    def analyze_faces(pil_image):
        return fai.get_gender_and_age_from_image(pil_image)

# used to get properties of the selected style liek prompt or strangth
# will be filled while interface is loading
style_details = {}


def action_session_initialized(request: gr.Request, state_dict: dict) -> None:
    """Initialize analytics session when app loads.
    
    Args:
        request (gr.Request): The Gradio request object containing client information
        state_dict (dict): The current application state dictionary
    """
    if not config.is_analytics_enabled() or not request:
        return

    app_state = AppState.from_dict(state_dict)
    try:
        analytics.save_session(
            session=app_state.session, 
            ip=request.client.host,
            user_agent=request.headers["user-agent"], 
            languages=request.headers["accept-language"])
        logger.info("Session initialized for: %s", request.client.host)
    except Exception as e:
        logger.error("Error initializing analytics session: %s", str(e))
        logger.debug("Exception details:", exc_info=True)

def action_update_all_local_models():
    """updates the list of available models in the ui"""
    return gr.update(choices=utils.get_all_local_models(config.get_model_folder()))

session_image_hashes = {}
def action_handle_input_file(request: gr.Request, image, state_dict):
    """Analyze the Image, Handle Session Info, Save the input image in a cache if enabled, count token."""
    global session_image_hashes
    app_state = AppState.from_dict(state_dict)
    # deactivate the start button on error
    if image is None: 
        return wrap_handle_input_response(app_state, False, "")
    # API Users don't have a request (by documentation)
    if not request: 
        return wrap_handle_input_response(app_state, False, "")

    input_file_path = ""
    image_sha1 = sha1(image.tobytes()).hexdigest()
    if config.is_input_cache_enabled():
        dir = config.get_output_folder()
        dir = os.path.join(dir, datetime.now().strftime("%Y%m%d"))
        input_file_path = utils.save_image_as_file(image, dir)

    image_description = ""
    try:
        image_description = action_describe_image(image)
    except Exception as e:
        logger.error("Error creating image description: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        gr.Warning("Could not create a proper description, please describe your image shortly")

    # variables used for analytics if enabled
    face_detected = False
    min_age = 0
    max_age = 0
    gender = -1
    new_token = 0 

    if config.is_feature_generation_with_token_enabled():
        #check that the image was not already used in this session
        skip_token = False
        if image_sha1 in session_image_hashes.keys():
            # check if the image is locked
            dt = session_image_hashes[image_sha1]
            if dt>datetime.now():
                gr.Warning(f"This image signature was already used to gain token. New token for it will be provided after {dt.strftime("%d.%m.%Y - %H:%M")}")
                skip_token = True
            else:
                #remove entry if it is outdated
                del session_image_hashes[image_sha1]
                #if the services is running for weeks wtith hundred of users, then it make sense to remove also other entries
                #FIXME: itterate over list and remove all old entries at once to free memory

        if not skip_token:
            session_image_hashes[image_sha1]=datetime.now()+timedelta(minutes=config.get_token_time_lock_for_new_image())
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
                for face in detected_faces:
                    #just save the jungest and oldest if we have multiple faces
                    min_age = face["minAge"] if face["minAge"]<min_age or min_age == 0 else min_age
                    max_age = face["maxAge"] if face["maxAge"]>max_age or max_age == 0 else max_age
                    if face["isFemale"]: # until we can recognize smiles
                        gender = 1 if gender == -1 else 2
                        if token_for_smiling>0:
                            logger.debug("Bonus: smiling")
                            new_token+=token_for_smiling
                            gr.Info(f"{token_for_smiling} special Bonus token added!")
                            token_for_smiling = 0 #apply only once per image
                    else:
                        # mal, 1 female, 2 both
                        gender = 0 if gender == -1 else 2

                    if token_for_cuteness>0 and (face["maxAge"]<20 or face["minAge"]>60):
                        logger.debug("Bonus: cuteness")
                        new_token+=token_for_cuteness
                        gr.Info(f"{token_for_cuteness} special Bonus token added!")
                        token_for_cuteness = 0 #allow bonus only once per upload
            
            gr.Info(f"Total new Token: {new_token}")
            app_state.token += new_token
    
    analytics.save_input_image_details(
        session=app_state.session, 
        sha1=image_sha1, 
        token=new_token,
        cache_path_and_filename=os.path.relpath(input_file_path, config.get_output_folder()), 
        face_detected=face_detected,
        min_age=min_age,
        max_age=max_age,
        gender=gender
        )
    start_enabled = True if not config.is_feature_generation_with_token_enabled() else bool(app_state.token>0)
    return wrap_handle_input_response(app_state, start_enabled, image_description)

def action_describe_image(image):
    """describe an image for better inpaint results."""
    if config.SKIP_AI: return "ai deactivated"
    
    value = AI.describe_image(image)
    logger.debug("Image description: %s", value)
    return value


def action_reload_model(model):
    if config.SKIP_AI: return
    logger.info("Reloading model %s", model)
    try:
        AI.change_text2img_model(model=model)
        gr.Info(message=f"Model {model} loaded.", title="Model changed")
    except Exception as e:
        gr.Error(message=e.message)

def action_generate_image(request: gr.Request, image, style, strength, steps, image_description, state_dict):
    """Convert the entire input image to the selected style."""
    global style_details
    app_state = AppState.from_dict(state_dict)
    #setting token always to 10 if the feature is disabled saved a lot of "if feature enabled .." statements
    if app_state.token == None: app_state.token = 0 
    if not config.is_feature_generation_with_token_enabled(): app_state.token = 10

    try:
        if config.is_feature_generation_with_token_enabled() and app_state.token<=0:
            gr.Warning("You have not enough token to start a generation. Upload a new image for new token!")
            return wrap_generate_image_response(app_state, image)
        if image is None: 
            gr.Error("Start of Generation without image!")
            return wrap_generate_image_response(app_state, None)
        # API Users don't have a request object (by documentation)
        if request is None: 
            logger.warning("No request object. API usage?")
            return wrap_generate_image_response(app_state, None)

        logger.debug("Starting image generation")
        if image_description == None or image_description == "": image_description = AI.describe_image(image)

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
        
        logger.info("%s - %s: %s - %s", datetime.now().strftime("%H:%M"), request.client.host, style, image_description)

        # must be before resizing, otherwise hash will not be same as from source image
        # or adapt the source image saving with thumbnail property
        image_sha1 = sha1(image.tobytes()).hexdigest()

        # use always the sliders for strength and steps if they are enabled
        if not config.UI_show_stength_slider(): strength = sd["strength"]
        if not config.UI_show_steps_slider(): steps = sd["steps"]

        if config.SKIP_AI:
            result_image = utils.image_convert_to_sepia(image)
            time.sleep(5)
        else:
            # Generate new picture
            result_image = AI.generate_image(
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
            analytics.save_generation_details(
                app_state.session,
                sha1=image_sha1,
                style=style,
                prompt=image_description,
                output_filename=os.path.relpath(fn, config.get_output_folder())
                )
        app_state.token -= 1
        if app_state.token <= 0: gr.Warning("You running out of Token.\n\nUpload a new image to continue.")
        return wrap_generate_image_response(app_state, result_image)
    except RuntimeError as e:
        logger.error("RuntimeError: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        gr.Error(e)
        return wrap_generate_image_response(app_state, None)

#--------------------------------------------------------------
# Gradio - Render UI
#--------------------------------------------------------------
def wrap_handle_input_response(app_state: AppState, start_enabled: bool, image_description: str) -> list:
    """Create a consistent response format for handle_input_file action.
    
    Args:
        app_state: The current AppState object
        start_enabled: Whether the start button should be enabled
        image_description: The generated image description
        
    Returns:
        List of values in the order: [start_button, text_description, local_storage, area_description, token_counter]
    """
    return [
        gr.update(interactive=start_enabled),
        image_description,
        app_state.to_dict(),
        gr.update(visible=True),
        app_state.token
    ]

def wrap_generate_image_response(app_state: AppState, result_image: any) -> list:
    """Create a consistent response format for generate_image action.
    
    Args:
        app_state: The current AppState object
        result_image: The generated image result
        
    Returns:
        List of values in the order: [output_image, local_storage, start_button, token_counter]
    """
    return [
        result_image,
        app_state.to_dict(),
        gr.update(interactive=bool(app_state.token>0)),
        app_state.token
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
                local_storage = gr.BrowserState(AppState()) # initial state with token=0 and new session
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
                    text_description = gr.Textbox(label="change the image description for better results", show_label=True, max_length=70, submit_btn="↻")

            with gr.Column():
                output_image = gr.Image(label="Result", type="pil", height=512)
                start_button = gr.Button("Start Creation", interactive=False, variant="primary")
                
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
                strength_slider = gr.Slider(label="Strength", minimum=0.1, maximum=1, value=config.get_default_strength(), step=0.1,  visible=config.UI_show_stength_slider())
                steps_slider = gr.Slider(label="Steps", minimum=10, maximum=100, value=config.get_default_steps(), step=5, visible=config.UI_show_steps_slider())

        def helper_display_token(token):
            return f"Current Token: {token}"
        
        @app.load(inputs=[local_storage], outputs=[token_counter])
        def load_from_local_storage(request: gr.Request, state_dict):
            # Initialize session when app loads
            action_session_initialized(request=request, state_dict=state_dict)
            
            # Restore token from local storage
            app_state = AppState.from_dict(state_dict)
            if config.is_feature_generation_with_token_enabled(): 
                logger.debug("Restoring token from local storage: %s", app_state.token)
                logger.debug("Session ID: %s", app_state.session)
            return app_state.token

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
            batch=False,
            max_batch_size=config.GenAI_get_execution_batch_size(),
            concurrency_id="gpu_queue"
        )

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
