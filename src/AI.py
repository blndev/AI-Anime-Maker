import src.utils as utils
from PIL import Image, ImageDraw
from hashlib import sha1
import src.config as config
from datetime import datetime
device = "cpu"  # will be checked and set in main functions

if not config.SKIP_AI:
    import gradio as gr
    import torch
    from transformers import pipeline  # for captioning
    from xformers.ops import MemoryEfficientAttentionFlashAttentionOp
    from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
    device = "cuda" if torch.cuda.is_available() else "cpu"


def check_safety(x_image):
    """Support function to check if the image is NSFW."""
    # all images are SFW ;)
    return x_image, False

#cache for image to text model
IMAGE_TO_TEXT_PIPELINE = None

def _load_captioner_model():
    """Load and return a image to text model."""
    if (IMAGE_TO_TEXT_PIPELINE != None):
        return IMAGE_TO_TEXT_PIPELINE

    # this will load teh model. if it is not availabole it will be downloaded from huggingface
    captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
    # TODO V3: change to this pipeline to query details about the image in Version 2
    # captioner = pipeline("image-text-to-text", model="Salesforce/blip-image-captioning-base")
    return captioner


def describe_image(image):
    """describe an image for better inpaint results."""
    try:
        captioner = _load_captioner_model()
        # TODO V3: add prompt to captioner to ask for details like how many people, background etc.
        # messages = [
        # {
        #     "role": "user",
        #     "content": [
        #         {"type": "image", "image": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg"},
        #         {"type": "text", "text": "What do we see in this image?"},
        #     ]
        # }]
        # prompt = captioner.apply_chat_template(messages)
        # value = captioner(image, text=prompt, return_full_text=False)
        value = captioner(image)
        return value[0]['generated_text']
    except Exception as e:
        print("Error while creating image description", e)
        return ""

#cache of the image loaded already
IMAGE_TO_IMAGE_PIPELINE = None

def _load_img2img_model(model=config.get_model(), use_cached_model=True):
    """Load and return the Stable Diffusion model to generate images"""
    global IMAGE_TO_IMAGE_PIPELINE
    if (IMAGE_TO_IMAGE_PIPELINE != None and use_cached_model):
        if config.DEBUG:
            print("using cached model")
        return IMAGE_TO_IMAGE_PIPELINE

    try:
        # TODO V3: support SDXL or FLux
        if config.DEBUG:
            print(f"create pipeline for model {model}")

        pipeline = None
        if model.endswith("safetensors"):
            if config.DEBUG:
                print("use 'from_single_file' to load model from local folder")
            pipeline = StableDiffusionImg2ImgPipeline.from_single_file(
                model,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                safety_checker=None, requires_safety_checker=False,
                use_safetensors=True
                # revision="fp16" if device == "cuda" else "",
            )
        else:
            if config.DEBUG:
                print("use 'from_pretrained' option to load model from hugging face")
            pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                model,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                safety_checker=None, requires_safety_checker=False)

        if config.DEBUG:
            print(f"--> pipeline initiated")
        pipeline = pipeline.to(device)
        if device == "cuda":
            pipeline.enable_xformers_memory_efficient_attention()
        if config.DEBUG:
            print("--> pipeline created")
        return pipeline
    except Exception as e:
        print(f"pipeline not be created. Error in load_model: {e}")
        raise Exception(message="Error while loading the model.\nSee logfile for details.")


def change_text2img_model(model):
    global IMAGE_TO_IMAGE_PIPELINE
    print(f"Reload model {model}")
    try:
        # TODO (low prio): check better ways to unload a model!
        IMAGE_TO_IMAGE_PIPELINE = None
        if device == "cuda":
            torch.cuda.empty_cache()
        # load new model
        IMAGE_TO_IMAGE_PIPELINE = _load_img2img_model(model=model, use_cached_model=False)
        if IMAGE_TO_IMAGE_PIPELINE is None:
            raise Exception("Pipeline is none")
    except Exception as e:
        print(f"Error while change_text2img_model: {e}")
        raise(f"Loading new img2img model '{model}' failed", e)



def generate_image(image: Image, prompt: str, negative_prompt: str = "", strength: float = 0.5, steps: int = 60):
    """Convert the entire input image to the selected style."""
    try:
        if image is None:
            raise Exception("no image provided")
        # API Users don't have a request (by documentation)

        if config.DEBUG:
            print("start AI.generate_image")

        model = _load_img2img_model()
        
        if (not config.SKIP_AI and model == None):
            print("error: no model loaded")
            raise Exception(message="No model loaded. Generation not available")

        # TODO Render previews in Version 2
        max_size = config.get_max_size()
        image.thumbnail((max_size, max_size))

        # create a mask which covers the whole image
        mask = Image.new("L", image.size, 255)

        if config.DEBUG:
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

        return result_image

    except RuntimeError as e:
        print(f"RuntimeError: {e}")
        raise Exception(message="Error while creating the image. More details in log.")
