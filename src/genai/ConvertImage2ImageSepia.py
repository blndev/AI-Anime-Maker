import gc
import logging
from typing import List
from PIL import Image
import numpy as np
from src.genai.ImageGenerationParameters import Image2ImageParameters
from src.utils.singleton import singleton
from .BaseGenAIHandler import BaseGenAIHandler

logger = logging.getLogger(__name__)

@singleton
class ConvertImage2ImageSimple(BaseGenAIHandler):
    """Simple Implementation without AI Pipelines to test the UI and App behavior"""
    def __init__(self, default_model: str = None, max_size: int = 1024):
        logger.info("Initialize ConvertImage2ImageSimple")
        self.max_image_size = max_size

    def __del__(self):
        logger.info("cleanup ConvertImage2ImageSimple")
        gc.collect()

    def _apply_sepia(self, image: Image.Image) -> Image.Image:
        """Convert an image to sepia tone."""
        # Convert the image to numpy array
        img_array = np.array(image)
        
        # Ensure image is RGB
        if len(img_array.shape) == 2:  # Grayscale
            img_array = np.stack((img_array,) * 3, axis=-1)
        
        # Extract RGB channels
        r = img_array[:,:,0]
        g = img_array[:,:,1]
        b = img_array[:,:,2]
        
        # Calculate sepia tone values
        sepia_r = (0.393 * r + 0.769 * g + 0.189 * b).clip(0, 255)
        sepia_g = (0.349 * r + 0.686 * g + 0.168 * b).clip(0, 255)
        sepia_b = (0.272 * r + 0.534 * g + 0.131 * b).clip(0, 255)
        
        # Merge channels
        sepia_array = np.stack([sepia_r, sepia_g, sepia_b], axis=2).astype(np.uint8)
        
        # Handle alpha channel if present
        if img_array.shape[2] == 4:
            sepia_array = np.dstack((sepia_array, img_array[:,:,3]))
        
        return Image.fromarray(sepia_array)

    def generate_image(self, params: Image2ImageParameters) -> Image.Image:
        """Convert the input image to sepia tone using parameter object"""
        try:
            # Validate parameters
            params.validate()
            
            logger.debug("starting sepia conversion")
            
            image = params.input_image
            # Resize if needed
            if image.size[0] > self.max_image_size or image.size[1] > self.max_image_size:
                image.thumbnail((self.max_image_size, self.max_image_size))

            # Convert to sepia
            result_image = self._apply_sepia(image)
            
            return result_image

        except Exception as e:
            logger.error("Error while generating sepia image: %s", str(e))
            raise Exception(f"Error while creating the sepia image: {e}")

    def generate_images(self, count: int) -> List[Image.Image]:
        """Not implemented for simple conversion."""
        raise NotImplementedError("Multiple image generation not supported for simple conversion")

    def generate_image_new(self) -> Image.Image:
        """Not implemented for simple conversion."""
        raise NotImplementedError("New image generation not supported for simple conversion")

    def ui_elements(self) -> dict:
        """Return a dictionary of UI elements and their required status."""
        return {
            "image": True,
            "prompt": False,
            "negative_prompt": False,
            "strength": False,
            "steps": False
        }

