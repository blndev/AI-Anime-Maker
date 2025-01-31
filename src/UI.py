import gradio as gr
from hashlib import sha1
import time # for sleep in SKIP_AI
from datetime import datetime

import src.config as config
import src.utils as utils
import src.analytics as analytics
import src.AI as AI

FAKE_AI_DELAY = 5 # time how long the thread sleeps to simulate generation

style_details = {}


def action_update_all_local_models():
    """updates the list of available models in the ui"""
    return gr.update(choices=utils.get_all_local_models(config.get_model_folder()))

def action_save_input_file(request: gr.Request, image):
    """Save the input image in a cache directory using its SHA-1 hash."""
    # deactivate the start buttons
    if image is None: return [gr.update(interactive=False), gr.update(interactive=False), ""]
    
    # API Users don't have a request (by documentation)
    if not request: return

    if config.is_analytics_enabled:
        try:
            analytics.save_session(
                session=request.session_hash, 
                ip=request.client.host,
                user_agent=request.headers["user-agent"], 
                languages=request.headers["accept-language"])
            if config.DEBUG:
                print("new image uploaded from: ", request.client.host)
        except Exception as e:
            print("Error for analytics", e)

    if config.is_cache_enabled():
        dir = config.get_cache_folder()
        utils.save_image_as_file(image, dir)

    image_description = AI.describe_image(image)
    # there is an image, activate the start buttons
    # TODO switch visibility for image description!
    return [gr.update(interactive=True), gr.update(interactive=True), image_description]

def action_describe_image(image):
    """describe an image for better inpaint results."""
    if config.SKIP_AI: return "ai deactivated"
    
    value = AI.describe_image(image)
    if config.DEBUG: print(f"Image description: {value}")
    return value


def action_reload_model(model):
    if config.SKIP_AI: return
    print (f"Reload model {model}")
    try:
        AI.change_text2img_model(model=model)
        gr.Info(message=f"Model {model} loaded.", title="Model changed")
    except Exception as e:
        gr.Error(message=e.message)

def action_generate_image(request: gr.Request, image, style, strength, steps, image_description):
    """Convert the entire input image to the selected style."""
    global style_details
    try:
        if image is None: return None, "no image"
        # API Users don't have a request (by documentation)
        if request is None: 
            print("Warning: no request object. API usage?")
            return None,"API forbidden"

        if config.DEBUG: print("start image generation")
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
        
        print (f"{datetime.now().strftime("%H:%M")} - {request.client.host}: {style} - {image_description}")

        # must be before resizing, otherwise hash will not be same as from source image
        # or adapt the source image saving with thumbnail property
        image_sha1 = sha1(image.tobytes()).hexdigest()

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
            fn = utils.save_image_with_timestamp(
                image=result_image,
                folder_path=config.get_output_folder(),
                reference=f"{image_sha1}-{style}",
                ignore_errors=True)

        if config.is_analytics_enabled():
            analytics.save_generation_details(
                request.session_hash,
                sha1=image_sha1,
                style=style,
                prompt=image_description,
                output_filename=fn
                )
        return result_image, image_description
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
        gr.Error(e)
        return None, image_description

#--------------------------------------------------------------
# Gradio - Render UI
#--------------------------------------------------------------
def create_gradio_interface():
    global style_details
    with gr.Blocks(
        title=config.get_app_title(), 
        css="footer {visibility: hidden}",
        analytics_enabled=False,
        theme=gr.themes.Soft()) as app:
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
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(label="Input Image", type="pil", height=512)
                describe_button = gr.Button("Describe your Image", interactive=False)
                text_description = gr.Textbox(label="use good but short image description for better results")
            with gr.Column():
                output_image = gr.Image(label="Output Image", type="pil", height=512)
                start_button = gr.Button("Start Creation", interactive=False)
                
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
                style_dropdown = gr.Radio(styles, label="Style", value="Anime")
                strength_slider = gr.Slider(label="Strength", minimum=0.1, maximum=1, value=config.get_default_strength(), step=0.1,  visible=config.UI_show_stength_slider())
                steps_slider = gr.Slider(label="Steps", minimum=10, maximum=100, value=config.get_default_steps(), step=5, visible=config.UI_show_steps_slider())


        # Save input image immediately on change
        image_input.change(
            fn=action_save_input_file,
            inputs=[image_input],
            outputs=[start_button, describe_button, text_description], 
            concurrency_limit=None,
        )

        describe_button.click(
            fn=action_describe_image,
            inputs=[image_input],
            outputs=[text_description],
            concurrency_limit=4,
            concurrency_id="describe"
        )

        start_button.click(
            fn=action_generate_image,
            inputs=[image_input, style_dropdown, strength_slider, steps_slider, text_description],
            outputs=[output_image, text_description],
            concurrency_limit=1,
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