from abc import ABC, abstractmethod
from typing import List
from PIL.Image import Image

from .ImageGenerationParameters import GenerationParameters


class BaseGenAIHandler(ABC):
    @abstractmethod
    def generate_images(self, params: GenerationParameters, count: int) -> List[Image]:
        """Generate a list of images."""
        pass

    def generate_image(self, params: GenerationParameters) -> Image:
        """Generate a single image by calling generate_images with count 1."""
        images = self.generate_images(params=params, count=1)
        if images:
            return images[0]
        else:
            return None

    @abstractmethod
    def ui_elements(self) -> dict:
        """Return a dictionary of UI elements and their required status."""
        pass


class ImageGenerationException(Exception):
    """Exception which can be raised if the image generation process failed."""
    def __init__(self, message, cause=None):
        super().__init__(message)
        self.message = message
        self.cause = cause
