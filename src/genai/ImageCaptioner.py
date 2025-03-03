import gc
import importlib
from PIL import Image
import logging
from src.utils.singleton import singleton
# Set up module logger
logger = logging.getLogger(__name__)


@singleton
class ImageCaptioner:
    def __init__(self):
        logger.info("Initialize ImageCaptioner")
        logger.debug("importing dependencies")
        try:
            self.torch = importlib.import_module("torch")
        except ModuleNotFoundError:
            logger.critical("Torch is not available")

        try:
            transformers = importlib.import_module("transformers")
            self.transformers_pipeline = getattr(transformers, 'pipeline')
            # self.transformers_pipeline = transformers.pipeline
        except ModuleNotFoundError:
            logger.critical("Transformers Module is not available")

        self.__load_captioner_model()

    def __del__(self):
        logger.info("free memory used for captioner")
        self.unload_pipeline()

    # cache for image to text model pipeline
    _cached_pipeline = None

    def __load_captioner_model(self):
        """Load and return a image to text model."""
        if (self._cached_pipeline):
            return self._cached_pipeline

        logger.info("Loading image-to-text pipline")
        # this will load the model. if it is not available it will be downloaded from huggingface
        # https://huggingface.co/Salesforce/blip-image-captioning-base
        # https://huggingface.co/docs/transformers/main_classes/pipelines#transformers.pipeline.task

        # processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        # model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to("cuda")

        self._cached_pipeline = self.transformers_pipeline(
            task="image-to-text",
            model="Salesforce/blip-image-captioning-base"
        )
        return self._cached_pipeline

    def unload_pipeline(self):
        try:
            logger.info("Unload image captioner")
            if self._cached_pipeline:
                del self._cached_pipeline
                self._cached_pipeline = None
                gc.collect()
            self.torch.cuda.empty_cache()
        except Exception:
            logger.error("Error while unloading captioner")

    def describe_image(self, image: Image):
        """describe an image for better inpaint results."""
        if not image:
            return ""

        if not isinstance(image, Image.Image):
            logger.warning(f"type of image is {type(image)}")
            return ""

        try:
            captioner = self.__load_captioner_model()
        except Exception:
            logger.warning("loading image captioner failed")
            self.unload_pipeline()

        try:
            if captioner:
                value = captioner(image)
                return value[0]['generated_text']
            else:
                return ""
        except Exception as e:
            logger.error("Error while creating image description.")
            logger.debug("Exception details:", e)
            return ""
