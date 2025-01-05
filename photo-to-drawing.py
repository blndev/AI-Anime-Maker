import gradio as gr
import torch
from hashlib import sha1
import os
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from PIL import Image, ImageDraw
from transformers import pipeline # for captioning
from xformers.ops import MemoryEfficientAttentionFlashAttentionOp

DEBUG = True

# TODO: load from config
#modelname = "./models/SD1.5/SFW/wildcardxRealistic_wildcardxV2.safetensors
#CURRENT_IMAGE_2_IMAGE_MODEL_NAME = "./models/wwtoonMix_v10.safetensors"
CURRENT_IMAGE_2_IMAGE_MODEL_NAME = "lavaman131/cartoonify"

models_folder = './models/'

def get_all_local_models():
    """read all local models to the system"""
    safetensors_files = []
    try:
        for root, _, files in os.walk(models_folder,followlinks=True):
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

device = "cuda" if torch.cuda.is_available() else "cpu"
print (f"running on {device}")

def save_input_file(image):
    """Save the input image in a cache directory using its SHA-1 hash."""
    if not os.path.exists("cache"):
        os.makedirs("cache")
    
    # deactivate the start buttons
    if image is None: return [gr.update(interactive=False), gr.update(interactive=False), ""]
    # if we use imageEditor from Gradio:
    # try:
    #     image = image['background'] # if we use editor field
    # except:
    #     print("seems no background in image dict")
    #     print (image)
    try:
        #print (image)
        # Convert the image to bytes and compute the SHA-1 hash
        image_bytes = image.tobytes()
        filetype = "jpg"
        filename_hash = sha1(image_bytes).hexdigest() + "."+filetype
        file_path = os.path.join("cache", filename_hash)

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
    # TODO: change to this pipeline to query details about the image in Version 2
    #captioner = pipeline("image-text-to-text", model="Salesforce/blip-image-captioning-base")
    return captioner

def describe_image(image):
    """describe an image for better inpaint results."""
    captioner = load_captioner()
    #TODO V3: add propmpt to captioner to ask for details like how many people, background etc.
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
def load_model(model=CURRENT_IMAGE_2_IMAGE_MODEL_NAME):
    """Load and return the Stable Diffusion model based on style."""
    global IMAGE_TO_IMAGE_PIPELINE
    if (IMAGE_TO_IMAGE_PIPELINE!= None): 
        if DEBUG: print ("using cached model")
        return IMAGE_TO_IMAGE_PIPELINE

    try:
        #TODO V3: support SDXL or FLux
        #pipeline = StableDiffusionPipeline.from_pretrained(
        #pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
        if DEBUG: print(f"create pipeline for model {model}")

        pipeline = None
        if model.endswith("safetensors"):
            if DEBUG: print("use 'from_single_file' to load model from local folder")
            pipeline = StableDiffusionImg2ImgPipeline.from_single_file(
                model,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                safety_checker = None, requires_safety_checker = False
                #use_safetensors=True
                #revision="fp16" if device == "cuda" else "",
            )
        else:
            if DEBUG: print("use 'from_pretrained' option to load model from hugging face")
            pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                model,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                safety_checker = None, requires_safety_checker = False)
            
        if DEBUG: print(f"- pipeline initiated")
        pipeline = pipeline.to(device)
        pipeline.enable_xformers_memory_efficient_attention()
        if DEBUG: print("-->pipeline created")
        return pipeline
    except Exception as e:
        print(f"pipeline not created. Error in load_model: {e}")
        if not gr is None:
            gr.Warning(message="Error while loading the model. See logfile for details.")


def debug_reload_model(model):
    if not DEBUG: return
    global IMAGE_TO_IMAGE_PIPELINE
    global CURRENT_IMAGE_2_IMAGE_MODEL_NAME
    print (f"Reload model {model}")
    try:
        IMAGE_TO_IMAGE_PIPELINE = None
        if device=="cuda": torch.cuda.empty_cache()
        IMAGE_TO_IMAGE_PIPELINE = load_model(model)
        if IMAGE_TO_IMAGE_PIPELINE is None: raise Exception("Pipeline is none")
        gr.Info(message=f"Model {model} loaded.", title="Model changed")
        CURRENT_IMAGE_2_IMAGE_MODEL_NAME = model
    except Exception as e:
        print(f"model not loaded. {e}")
        gr.Warning(message=f"Loading Model {model} failed. \n\n {e}")

def stylize(image, style, strength, steps, image_description):
    """Convert the entire input image to the selected style."""
    try:
        if image is None: return None, "no image"

        if DEBUG: print("start stylize")

        model = load_model()
        if image_description is None or image_description == "": image_description = describe_image(image)

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
            negative_prompt = "young people"
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

        # TODO: load from config
        image.thumbnail((1024,1024))
        #image.thumbnail((768,768))

        # create a mask which covers the whole image
        mask = Image.new("L", image.size, 255) 
        if DEBUG:
            print(f"Strength: {strength}, Steps: {steps}, Model: unkown")
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
        return result_image, image_description
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
        gr.Error(e)
        return None, image_description

# Gradio Starts
#---------------------------------------------------------------------------
# Render UI
#--------------------------------------------------------------
with gr.Blocks() as app:
    with gr.Row():
        #TODO: load from Config
        gr.Markdown("### Stable Diffusion Stylization")
    if DEBUG:
        gr.Markdown("*DEBUG enabled*")
        with gr.Row():
            with gr.Column():
                model_dropdown = gr.Dropdown(choices=get_all_local_models(), value=CURRENT_IMAGE_2_IMAGE_MODEL_NAME, label="Models")
            with gr.Column():
                refresh_model_list_button = gr.Button("refresh model list")
                reload_button = gr.Button("load model")
                reload_button.click(
                    fn=debug_reload_model,
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
            strength_slider = gr.Slider(label="Strength", minimum=0.1, maximum=1, value=0.4, step=0.1)
            steps_slider = gr.Slider(label="Steps", minimum=10, maximum=100, value=75, step=5)

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
        fn=stylize,
        inputs=[image_input, style_dropdown, strength_slider, steps_slider, text_description],
        outputs=[output_image, text_description]
    )

if __name__ == "__main__":
    IMAGE_TO_IMAGE_PIPELINE = load_model()
    IMAGE_TO_TEXT_PIPELINE = load_captioner()
    app.launch()