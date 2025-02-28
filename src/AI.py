import gc
from PIL import Image, ImageDraw
from hashlib import sha1
import logging
import src.config as config

# Set up module logger
logger = logging.getLogger(__name__)
device = "cpu"  # will be checked and set in main functions

if not config.SKIP_AI:
    import gradio as gr
    import torch
    from transformers import pipeline  # for captioning
    from xformers.ops import MemoryEfficientAttentionFlashAttentionOp
    from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Running on %s", device)



def check_safety(x_image):
    """Support function to check if the image is NSFW."""
    # all images are SFW ;)
    return x_image, False


# cache for image to text model
IMAGE_TO_TEXT_PIPELINE = None


def _load_captioner_model():
    """Load and return a image to text model."""
    global IMAGE_TO_TEXT_PIPELINE
    if (IMAGE_TO_TEXT_PIPELINE != None):
        return IMAGE_TO_TEXT_PIPELINE

    # this will load the model. if it is not available it will be downloaded from huggingface
    IMAGE_TO_TEXT_PIPELINE = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
    return IMAGE_TO_TEXT_PIPELINE

def _cleanup_captioner():
    global IMAGE_TO_TEXT_PIPELINE
    try:
        logger.info("Unload image captioner")
        if IMAGE_TO_TEXT_PIPELINE!= None:
            del IMAGE_TO_TEXT_PIPELINE
            IMAGE_TO_TEXT_PIPELINE = None
            gc.collect()
        
        torch.cuda.empty_cache()
        #TODO: there must be more to unload
    except Exception as e:
        logger.error("Error while unloading captioner")

def describe_image(image):
    """describe an image for better inpaint results."""
    try:
        captioner = _load_captioner_model()
    except Exception:
        logger.warn("loading image captioner failed")
        _cleanup_captioner()

    try:
        if captioner:
            value = captioner(image)
            return value[0]['generated_text']
        else:
            return ""
    except Exception as e:
        logger.error("Error while creating image description.")
        logger.debug("Exception details:", exc_info=True)
        return ""

# cache of the image loaded already
IMAGE_TO_IMAGE_PIPELINE = None


def _load_img2img_model(model=config.get_model(), use_cached_model=True):
    """Load and return the Stable Diffusion model to generate images"""
    #use cached becomes obsolete with a proper unloading!
    global IMAGE_TO_IMAGE_PIPELINE
    if (IMAGE_TO_IMAGE_PIPELINE != None and use_cached_model):
        logger.debug("Using cached model")
        return IMAGE_TO_IMAGE_PIPELINE

    try:
        # TODO V3: support SDXL or FLux
        logger.debug("Creating pipeline for model %s", model)

        pipeline = None
        if model.endswith("safetensors"):
            logger.debug("Using 'from_single_file' to load model from local folder")
            pipeline = StableDiffusionImg2ImgPipeline.from_single_file(
                model,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                safety_checker=None, requires_safety_checker=False,
                use_safetensors=True
                # revision="fp16" if device == "cuda" else "",
            )
        else:
            logger.debug("Using 'from_pretrained' option to load model from hugging face")
            pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                model,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                safety_checker=None, requires_safety_checker=False)

        logger.debug("Pipeline initiated")
        pipeline = pipeline.to(device)
        if device == "cuda":
            pipeline.enable_xformers_memory_efficient_attention()
        logger.debug("Pipeline created")
        IMAGE_TO_IMAGE_PIPELINE = pipeline
        return pipeline
    except Exception as e:
        logger.error("Pipeline could not be created. Error in load_model: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        raise Exception(message="Error while loading the model.\nSee logfile for details.")

def _cleanup_img2img_pipeline():
    global IMAGE_TO_IMAGE_PIPELINE
    try:
        logger.info("Unload image captioner")
        if IMAGE_TO_IMAGE_PIPELINE!= None:
            del IMAGE_TO_IMAGE_PIPELINE
            IMAGE_TO_IMAGE_PIPELINE = None
            gc.collect()
        
        torch.cuda.empty_cache()
        #TODO: there must be more to unload
    except Exception as e:
        logger.error("Error while unloading IMAGE_TO_IMAGE_PIPELINE")

def change_text2img_model(model):
    global IMAGE_TO_IMAGE_PIPELINE
    logger.info("Reloading model %s", model)
    try:
        # TODO (low prio): check better ways to unload a model!
        _cleanup_img2img_pipeline()
        # load new model
        IMAGE_TO_IMAGE_PIPELINE = _load_img2img_model(model=model, use_cached_model=False)
        if IMAGE_TO_IMAGE_PIPELINE is None:
            raise Exception("Pipeline is none")
    except Exception as e:
        logger.error("Error while changing text2img model: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        raise (f"Loading new img2img model '{model}' failed", e)


def generate_image(image: Image, prompt: str, negative_prompt: str = "", strength: float = 0.5, steps: int = 60):
    """Convert the entire input image to the selected style."""
    try:
        if image is None:
            raise Exception("no image provided")
        # API Users don't have a request (by documentation)

        logger.debug("Starting AI.generate_image")

        model = _load_img2img_model()

        if (not config.SKIP_AI and model == None):
            logger.error("No model loaded")
            raise Exception(message="No model loaded. Generation not available")

        max_size = config.get_max_size()
        image.thumbnail((max_size, max_size))

        # create a mask which covers the whole image
        mask = Image.new("L", image.size, 255)

        logger.debug("Strength: %f, Steps: %d", strength, steps)

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
        logger.error("RuntimeError: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        raise Exception(message="Error while creating the image. More details in log.")
        #todo: add error count, on 3 errors unload and reload the model
