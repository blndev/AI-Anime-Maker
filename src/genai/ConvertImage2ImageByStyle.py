import gc
import importlib
from PIL import Image
import logging
import src.config as config  # TODO: to find standard model (shold be handed over in init)

# Set up module logger
logger = logging.getLogger(__name__)


class ConvertImage2ImageByStyle:
    def __init__(self):
        logger.info("importing dependencies")
        try:
            self.torch = importlib.import_module("torch")
        except ModuleNotFoundError:
            logger.critical("Torch is not available")

        try:
            transformers = importlib.import_module("transformers")
            self.transformers_pipeline = getattr(transformers, 'pipeline')
            #self.transformers_pipeline = transformers.pipeline
        except ModuleNotFoundError:
            logger.critical("Torch is not available")

        try:
            diffusers = importlib.import_module("diffusers")
            self.StableDiffusionImg2ImgPipeline = diffusers.StableDiffusionImg2ImgPipeline
        except ModuleNotFoundError:
            logger.critical("Torch is not available")

        self.device = "cuda" if self.torch.cuda.is_available() else "cpu"
        logger.info("Running on %s", self.device)
        
    def check_safety(self, x_image):
        """Support function to check if the image is NSFW."""
        return x_image, False

    # cache of the image loaded already
    IMAGE_TO_IMAGE_PIPELINE = None

    def _load_img2img_model(self, model=config.get_model(), use_cached_model=True):
        """Load and return the Stable Diffusion model to generate images"""
        if (self.IMAGE_TO_IMAGE_PIPELINE and use_cached_model):
            logger.debug("Using cached model")
            return self.IMAGE_TO_IMAGE_PIPELINE

        try:
            # TODO V3: support SDXL or FLux
            logger.debug("Creating pipeline for model %s", model)

            pipeline = None
            if model.endswith("safetensors"):
                logger.info(f"Using 'from_single_file' to load model {model} from local folder")
                pipeline = self.StableDiffusionImg2ImgPipeline.from_single_file(
                    model,
                    torch_dtype=self.torch.float16 if self.device == "cuda" else self.torch.float32,
                    safety_checker=None, requires_safety_checker=False,
                    use_safetensors=True
                    # revision="fp16" if device == "cuda" else "",
                )
            else:
                logger.info(f"Using 'from_pretrained' option to load model {model} from hugging face")
                pipeline = self.StableDiffusionImg2ImgPipeline.from_pretrained(
                    model,
                    torch_dtype=self.torch.float16 if self.device == "cuda" else self.torch.float32,
                    safety_checker=None, requires_safety_checker=False)

            logger.debug("Pipeline initiated")
            pipeline = pipeline.to(self.device)
            if self.device == "cuda":
                pipeline.enable_xformers_memory_efficient_attention()
            logger.debug("Pipeline created")
            self.IMAGE_TO_IMAGE_PIPELINE = pipeline
            return pipeline
        except Exception as e:
            logger.error("Pipeline could not be created. Error in load_model: %s", str(e))
            logger.debug("Exception details:", exc_info=True)
            self._cleanup_img2img_pipeline()
            raise Exception(message="Error while loading the model.\nSee logfile for details.")

    def _cleanup_img2img_pipeline(self):
        try:
            logger.info("Unload image captioner")
            if self.IMAGE_TO_IMAGE_PIPELINE:
                del self.IMAGE_TO_IMAGE_PIPELINE
                self.IMAGE_TO_IMAGE_PIPELINE = None
                gc.collect()
            self.torch.cuda.empty_cache()
        except Exception:
            logger.error("Error while unloading IMAGE_TO_IMAGE_PIPELINE")

    def change_text2img_model(self, model):
        logger.info("Reloading model %s", model)
        try:
            self._cleanup_img2img_pipeline()
            # load new model
            self.IMAGE_TO_IMAGE_PIPELINE = self._load_img2img_model(model=model, use_cached_model=False)
            if self.IMAGE_TO_IMAGE_PIPELINE is None:
                raise Exception("Pipeline is none")
        except Exception as e:
            logger.error("Error while changing text2img model: %s", str(e))
            logger.debug("Exception details:", exc_info=True)
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
                raise Exception("no image provided")
            # API Users don't have a request (by documentation)

            logger.debug("Starting AI.generate_image")

            model = self._load_img2img_model()

            if (not model):
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
            logger.error("Error while genrating Image: %s", str(e))
            self._cleanup_img2img_pipeline()
            raise Exception(message="Error while creating the image. More details in log.")