import gradio as gr
import torch
from hashlib import sha1
import os
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from PIL import Image, ImageDraw
from transformers import pipeline # for captioning
from xformers.ops import MemoryEfficientAttentionFlashAttentionOp
import config
import utils

DEBUG = True

device = "cuda" # will be checked and set in main functions

def get_all_local_models():
    """read all local models to the system"""
    safetensors_files = []
    try:
        for root, _, files in os.walk(config.get_model_folder(),followlinks=True):
            for file in files:
                if file.endswith('.safetensors'):
                    relative_path = "./" + os.path.relpath(os.path.join(root, file))
                    safetensors_files.append(relative_path)
        print (safetensors_files)
    except Exception as e:
        print(e)
    return safetensors_files

def update_all_local_models():
    """updates the list of available models in the ui"""
    return gr.update(choices=get_all_local_models())

def save_input_file(image):
    """Save the input image in a cache directory using its SHA-1 hash."""
    # deactivate the start buttons
    if image is None or load_model()==None: return [gr.update(interactive=False), gr.update(interactive=False), ""]

    if config.is_cache_enabled():
        dir = config.get_cache_folder()
        if not os.path.exists(dir):
            os.makedirs(dir)
        # if we use imageEditor from Gradio:
        # try:
        #     image = image['background'] # if we use editor field
        # except:
        #     print("seems no background in image dict")
        #     print (image)
        try:
            # Convert the image to bytes and compute the SHA-1 hash
            image_bytes = image.tobytes()
            filetype = "jpg"
            filename_hash = sha1(image_bytes).hexdigest() + "."+filetype
            file_path = os.path.join(dir, filename_hash)

            if not os.path.exists(file_path):
                image.save(file_path, format="JPEG")

            if DEBUG: print(f"Image saved to \"{file_path}\"")

        except Exception as e:
            print(f"Error while saving image:\n{e}")

    # there is an image, activate the start buttons
    return [gr.update(interactive=True), gr.update(interactive=True), ""]


def check_safety(x_image):
    """Support function to check if the image is NSFW."""
    # all images are SFW ;)
    return x_image, False 

IMAGE_TO_TEXT_PIPELINE = None
def load_captioner():
    """Load and return a image to text model."""
    if (IMAGE_TO_TEXT_PIPELINE!= None): return IMAGE_TO_TEXT_PIPELINE

    captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
    # TODO V3: change to this pipeline to query details about the image in Version 2
    #captioner = pipeline("image-text-to-text", model="Salesforce/blip-image-captioning-base")
    return captioner

def describe_image(image):
    """describe an image for better inpaint results."""
    captioner = load_captioner()
    #TODO V3: add prompt to captioner to ask for details like how many people, background etc.
    # messages = [
    # {
    #     "role": "user",
    #     "content": [
    #         {"type": "image", "image": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg"},
    #         {"type": "text", "text": "What do we see in this image?"},
    #     ]
    # }]
    # prompt = captioner.apply_chat_template(messages)
    #value = captioner(image, text=prompt, return_full_text=False)
    value = captioner(image)
    if DEBUG: print(f"Image description: {value}")
    return value[0]['generated_text']

IMAGE_TO_IMAGE_PIPELINE = None
def load_model(model=config.get_model()):
    """Load and return the Stable Diffusion model based on style."""
    global IMAGE_TO_IMAGE_PIPELINE
    if (IMAGE_TO_IMAGE_PIPELINE!= None): 
        if DEBUG: print ("using cached model")
        return IMAGE_TO_IMAGE_PIPELINE

    try:
        #TODO V3: support SDXL or FLux
        if DEBUG: print(f"create pipeline for model {model}")

        pipeline = None
        if model.endswith("safetensors"):
            if DEBUG: print("use 'from_single_file' to load model from local folder")
            pipeline = StableDiffusionImg2ImgPipeline.from_single_file(
                model,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                safety_checker = None, requires_safety_checker = False,
                use_safetensors=True
                #revision="fp16" if device == "cuda" else "",
            )
        else:
            if DEBUG: print("use 'from_pretrained' option to load model from hugging face")
            pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                model,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                safety_checker = None, requires_safety_checker = False)
            
        if DEBUG: print(f"--> pipeline initiated")
        pipeline = pipeline.to(device)
        if device=="cuda": pipeline.enable_xformers_memory_efficient_attention()
        if DEBUG: print("--> pipeline created")
        return pipeline
    except Exception as e:
        print(f"pipeline not created. Error in load_model: {e}")
        if not gr is None:
            gr.Error(message="Error while loading the model.\nSee logfile for details.")
        return None


def action_reload_model(model):
    if not DEBUG: return
    global IMAGE_TO_IMAGE_PIPELINE
    print (f"Reload model {model}")
    try:
        # TODO: check better ways to unload a model!
        IMAGE_TO_IMAGE_PIPELINE = None
        if device=="cuda": torch.cuda.empty_cache()
        # load new model
        IMAGE_TO_IMAGE_PIPELINE = load_model(model)
        if IMAGE_TO_IMAGE_PIPELINE is None: raise Exception("Pipeline is none")
        gr.Info(message=f"Model {model} loaded.", title="Model changed")
    except Exception as e:
        print(f"model not loaded. {e}")

def action_generate_image(image, style, strength, steps, image_description):
    """Convert the entire input image to the selected style."""
    try:
        if image is None: return None, "no image"

        if DEBUG: print("start stylize")

        model = load_model()
        if image_description == None or image_description == "": image_description = describe_image(image)

        if (model == None): 
            gr.Error(message="No model loaded. Generation not available")
            return None, ""
        
        # TODO V2: write statistics about the used styles (how much used)
        negative_prompt = ""
        # Adjust the prompt based on style
        # TODO: load prompts and styles fdrom config
        if style == "Anime":
            prompt = "Perfect anime quality, modern, colorful, anime style, flowers, Japanese objects, smiling"
            negative_prompt = "realistic photo, asian"
            strength = 0.5
        elif style == "Pixar":
            prompt = "A beautiful scene from a pixar cartoon, perfect drawing, many details, smiling, perfect eyes"
            negative_prompt = "realistic photo"
            strength = 0.5
        elif style == "Manga":
            prompt = "manga style, perfect drawing,smiling"
            negative_prompt = "realistic photo"
            strength = 0.5
        elif style == "Painting":
            prompt = "modern oil painting, smiling"
            strength = 0.5
            negative_prompt = "realistic photo"
        elif style == "Fantasy":
            prompt = "A detailed digital illustration in the style of Dimitry Roulland, The animation illustration style combines realistic details with a whimsical touch, characteristic of Roulland's style"
        elif style == "Old":
            prompt = "photo of very old "
            strength = 0.6
            if (image_description.startswith("a ")): image_description = image_description[2:]
            #negative_prompt = "young people"
        elif style == "Young":
            prompt = "very detailed modern photo from childhood with perfect faces and shy smiles"  
            if (image_description.startswith("a ")): image_description = image_description[2:]
            strength = 0.6
            negative_prompt = "old people"
        else:
            # just use description for creativity purpose 
            prompt = ""
            negative_prompt = ""
        
        prompt += f": {image_description}"

        print (prompt)

        # TODO Render previews in Version 2

        max_size = config.get_max_size()
        image.thumbnail((max_size,max_size))

        # create a mask which covers the whole image
        mask = Image.new("L", image.size, 255) 
        if DEBUG:
            print(f"Strength: {strength}, Steps: {steps}")
        # Generate new picture
        result_image = model(
            prompt=prompt, 
            negative_prompt=negative_prompt,
            num_inference_steps=steps, 
            image=image,
            mask_image=mask, 
            strength=strength,
            ).images[0]
        # TODO: save file first (config option to tun it of)
        if config.is_save_output_enabled():
            utils.save_image_with_timestamp(result_image,config.get_output_folder(), ignore_errors=True)

        return result_image, image_description
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
        gr.Error(e)
        return None, image_description

def create_gradio_interface():
    # Gradio Starts
    #---------------------------------------------------------------------------
    # Render UI
    #--------------------------------------------------------------
    with gr.Blocks(title=config.get_app_title()) as app:
        with gr.Row():
            gr.Markdown("### " + config.get_app_title()+"\n\n" + config.get_user_message())
            
        if DEBUG:
            gr.Markdown("*DEBUG enabled*")
            with gr.Row():
                with gr.Column():
                    model_dropdown = gr.Dropdown(choices=get_all_local_models(), value=config.get_model(), label="Models", allow_custom_value=True)
                with gr.Column():
                    refresh_model_list_button = gr.Button("refresh model list")
                    reload_button = gr.Button("load model")
                    reload_button.click(
                        fn=action_reload_model,
                        inputs=[model_dropdown],
                        outputs=[]
                    )
                    refresh_model_list_button.click(
                        fn=update_all_local_models,
                        inputs=[],
                        outputs=[model_dropdown]
                    )
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(label="Input Image", type="pil", height=512)
                describe_button = gr.Button("Describe", interactive=False)
                text_description = gr.Textbox(label="Image description for better results")
            with gr.Column():
                #TODO: load from config
                styles = [
                    "Anime",
                    "Manga",
                    "Pixar",
                    "Painting",
                    "Fantasy",
                    "Old",
                    "Young"
                ]
                output_image = gr.Image(label="Output Image", type="pil", height=512)
                if DEBUG: styles.append("Open Style")
                style_dropdown = gr.Radio(styles, label="Style", value="Anime")
                strength_slider = gr.Slider(label="Strength", minimum=0.1, maximum=1, value=config.get_default_strengths(), step=0.1,  visible=config.UI_show_stengths_slider())
                steps_slider = gr.Slider(label="Steps", minimum=10, maximum=100, value=config.get_default_steps(), step=5, visible=config.UI_show_steps_slider())

                start_button = gr.Button("Create", interactive=False)

        # Save input image immediately on change
        image_input.change(
            fn=save_input_file,
            inputs=[image_input],
            outputs=[start_button, describe_button, text_description]
        )

        describe_button.click(
            fn=describe_image,
            inputs=[image_input],
            outputs=[text_description]
        )

        start_button.click(
            fn=action_generate_image,
            inputs=[image_input, style_dropdown, strength_slider, steps_slider, text_description],
            outputs=[output_image, text_description]
        )

        return app

if __name__ == "__main__":
    try:
        if config.read_configuration() == None: print("read configuration failed")
        model = config.get_model()
        if model.endswith("safetensors"):
            utils.download_file(url=config.get_model_url(), local_path=model)

        print ("initializing ai models")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print (f"running on {device}")

        IMAGE_TO_IMAGE_PIPELINE = load_model()
        IMAGE_TO_TEXT_PIPELINE = load_captioner()
        print ("starting " + config.get_app_title())
        app = create_gradio_interface()
        app.launch(share = config.is_gradio_shared())
    except Exception as e:
        print (e)
        print ("app closed")