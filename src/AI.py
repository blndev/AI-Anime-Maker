from datetime import datetime
import gradio as gr
import torch
from hashlib import sha1
import os
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from PIL import Image, ImageDraw
from transformers import pipeline # for captioning
from xformers.ops import MemoryEfficientAttentionFlashAttentionOp
import time # for sleep in FAKE_AI

import src.config as config
import src.utils as utils
import src.analytics as analytics

# if active much more log output and ability to switch and select the used generation model 
DEBUG = False
# if active the system is not using any AI, just simulating the funcion
FAKE_AI = True
FAKE_AI_DELAY = 5 # time how long the thread sleeps to simulate generation

device = "cuda" # will be checked and set in main functions
style_details = {}

#TODO: Refactor and use logger instead
utils.DEBUG = DEBUG
analytics.DEBUG = DEBUG

def check_safety(x_image):
    """Support function to check if the image is NSFW."""
    # all images are SFW ;)
    return x_image, False 

IMAGE_TO_TEXT_PIPELINE = None
def _load_captioner():
    """Load and return a image to text model."""
    if FAKE_AI: return
    if (IMAGE_TO_TEXT_PIPELINE!= None): return IMAGE_TO_TEXT_PIPELINE

    #TODO: check stop params like 
    captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
    # TODO V3: change to this pipeline to query details about the image in Version 2
    #captioner = pipeline("image-text-to-text", model="Salesforce/blip-image-captioning-base")
    return captioner

def describe_image(image):
    """describe an image for better inpaint results."""
    try:
        captioner = _load_captioner()
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
        return value[0]['generated_text']
    except Exception as e:
        print ("Error while creating image description", e)
        return ""

IMAGE_TO_IMAGE_PIPELINE = None
def _load_test2img_model(model=config.get_model()):
    """Load and return the Stable Diffusion model based on style."""
    if FAKE_AI: return False

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
        print(f"pipeline not be created. Error in load_model: {e}")
        raise Exception(message="Error while loading the model.\nSee logfile for details.")


def change_text2img_model(model):
    if FAKE_AI: return
    global IMAGE_TO_IMAGE_PIPELINE
    print (f"Reload model {model}")
    try:
        # TODO (low prio): check better ways to unload a model!
        IMAGE_TO_IMAGE_PIPELINE = None
        if device=="cuda": torch.cuda.empty_cache()
        # load new model
        IMAGE_TO_IMAGE_PIPELINE = _load_test2img_model(model)
        if IMAGE_TO_IMAGE_PIPELINE is None: raise Exception("Pipeline is none")
        gr.Info(message=f"Model {model} loaded.", title="Model changed")
    except Exception as e:
        print(f"Error while change_text2img_model: {e}")

def generate_image(image, prompt, negative_prompt, strength, steps):
    """Convert the entire input image to the selected style."""
    global style_details
    try:
        if image is None: return None, "no image"
        # API Users don't have a request (by documentation)

        if DEBUG: print("start AI.generate_image")
        model = _load_test2img_model()
        if image_description == None or image_description == "": image_description = action_describe_image(image)

        #TODO: check image_description
        if (not FAKE_AI and model == None): 
            print("error: no model loaded")
            gr.Error(message="No model loaded. Generation not available")
            return None, ""

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
        
        return result_image
    
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
        raise Exception(message="Error while creating the image")
