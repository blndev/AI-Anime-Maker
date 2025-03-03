from abc import ABC, abstractmethod
from typing import List
from PIL import Image


class BaseGenAIHandler(ABC):
    @abstractmethod
    def generate_images(self, count: int) -> List[Image.Image]:
        """Generate a list of images."""
        pass

    def generate_image(self) -> Image.Image:
        """Generate a single image by calling generate_images with count 1."""
        images = self.generate_images(1)
        return images[0] if images else None

    @abstractmethod
    def ui_elements(self) -> dict:
        """Return a dictionary of UI elements and their required status."""
        pass
