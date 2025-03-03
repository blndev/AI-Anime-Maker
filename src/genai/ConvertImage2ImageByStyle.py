import gc
import importlib
from typing import List
from PIL import Image
import logging
from src.utils.singleton import singleton
from .BaseGenAIHandler import BaseGenAIHandler, ImageGenerationException
import threading
import src.config as config  # TODO: to find standard model (shold be handed over in init)

# Set up module logger
logger = logging.getLogger(__name__)

#@singleton
class ConvertImage2ImageByStyle(BaseGenAIHandler):
    def __init__(self, default_model: str, max_size: int = 1024):
        logger.info("Initialize ConvertImage2ImageByStyle")
        logger.debug("importing dependencies")
        try:
            self.torch = importlib.import_module("torch")
        except ModuleNotFoundError:
            logger.critical("Torch is not available")

        try:
            transformers = importlib.import_module("transformers")
            self.transformers_pipeline = transformers.pipeline
        except ModuleNotFoundError:
            logger.critical("Torch is not available")

        try:
            diffusers = importlib.import_module("diffusers")
            self.StableDiffusionImg2ImgPipeline = diffusers.StableDiffusionImg2ImgPipeline
        except ModuleNotFoundError:
            logger.critical("Diffusers Modul is not available")

        self.max_image_size = max_size
        self.default_model = default_model
        self.device = "cuda" if self.torch.cuda.is_available() else "cpu"

    def __del__(self):
        logger.info("free memory used for ConvertImage2ImageByStyle pipeline")
        self.unload_img2img_pipeline()
        
    def check_safety(self, x_image):
        """Support function to check if the image is NSFW."""
        return x_image, False

    # cache of the image loaded already
    _cached_img2img_pipeline = None

    def _load_img2img_model(self, model=config.get_model(), use_cached_model=True):
        """Load and return the Stable Diffusion model to generate images"""
        if (self._cached_img2img_pipeline and use_cached_model):
            return self._cached_img2img_pipeline

        try:
            # TODO V3: support SDXL or FLux
            logger.debug(f"Loading img2img model {model}")

            pipeline = None
            if model.endswith("safetensors"):
                logger.info(f"Using 'from_single_file' to load model {model} from local folder")
                pipeline = self.StableDiffusionImg2ImgPipeline.from_single_file(
                    model,
                    torch_dtype=self.torch.float16 if self.device == "cuda" else self.torch.float32,
                    safety_checker=None,
                    requires_safety_checker=False,
                    use_safetensors=True
                )
            else:
                logger.info(f"Using 'from_pretrained' option to load model {model} from hugging face")
                pipeline = self.StableDiffusionImg2ImgPipeline.from_pretrained(
                    model,
                    torch_dtype=self.torch.float16 if self.device == "cuda" else self.torch.float32,
                    safety_checker=None,
                    requires_safety_checker=False
                )

            logger.debug("diffuser initiated")
            pipeline = pipeline.to(self.device)
            if self.device == "cuda":
                pipeline.enable_xformers_memory_efficient_attention()
            logger.debug("ConvertImage2ImageByStyle-Pipeline created")
            self._cached_img2img_pipeline = pipeline
            return pipeline
        except Exception as e:
            logger.error("Img2Img Pipeline could not be created. Error in load_model: %s", str(e))
            logger.debug("Exception details:", e)
            self.unload_img2img_pipeline()
            raise Exception(message="Error while loading the pipline for image conversion.\nSee logfile for details.")

    def unload_img2img_pipeline(self):
        try:
            logger.info("Unload image captioner")
            if self._cached_img2img_pipeline:
                del self._cached_img2img_pipeline
                self._cached_img2img_pipeline = None
            gc.collect()
            self.torch.cuda.empty_cache()
        except Exception:
            logger.error("Error while unloading IMAGE_TO_IMAGE_PIPELINE")

    def change_img2img_model(self, model):
        logger.info("Reloading model %s", model)
        try:
            self.default_model = model
            self.unload_img2img_pipeline()
            self._load_img2img_model(model=model, use_cached_model=False)
        except Exception as e:
            logger.error("Error while changing text2img model: %s", str(e))
            logger.debug("Exception details: {e}")
            raise (f"Loading new img2img model '{model}' failed", e)

    def generate_image(self,
                       image: Image,
                       prompt: str,
                       negative_prompt: str = "",
                       strength: float = 0.5,
                       steps: int = 60):
        """Convert the entire input image to the selected style."""
        try:
            if image is None:
                raise ValueError("no image provided")

            if strength<0.1 or strength>1:
                raise ValueError("strength must be >0 and <1")

            if steps<=0 or steps>=100:
                raise ValueError("steps must be >0 and <100")

            if not prompt:
                prompt=""

            logger.debug("starting image generation")
            model = self._load_img2img_model()
            if (not model):
                logger.error("No model loaded")
                raise Exception(message="No model loaded. Generation not available")

            max_size = self.max_image_size
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
            logger.error("Error while genrating Image: %s", str(e))
            self.unload_img2img_pipeline()
            msg = e.message
            raise ImageGenerationException(message=f"Error while creating the image. {msg}")
        
    def generate_images(self, count: int) -> List[Image.Image]:
        """Generate a list of images."""
        pass

    def generate_image_new(self) -> Image.Image:
        """Generate a single image by calling generate_images with count 1."""
        images = self.generate_images(1)
        return images[0] if images else None

    def ui_elements(self) -> dict:
        """Return a dictionary of UI elements and their required status."""
        pass
