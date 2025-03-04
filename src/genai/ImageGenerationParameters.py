from dataclasses import dataclass, field
from typing import Optional, Union
from PIL import Image
import logging

logger = logging.getLogger(__name__)
"""
Usage examples:

# For simple sepia conversion
params = Image2ImageParameters(
    input_image=original_image,
    strength=0.7
)
sepia_image = simple_converter.generate_image(params)

# For AI style transfer
style_params = Image2ImageParameters(
    input_image=original_image,
    prompt="anime style, detailed",
    negative_prompt="blurry, low quality",
    strength=0.75,
    steps=50,
    mask_image=mask_image  # optional
)
styled_image = style_converter.generate_image(style_params)

# For text-to-image generation
text_params = Text2ImageParameters(
    prompt="a beautiful sunset",
    negative_prompt="blurry, low quality",
    steps=50,
    width=768,
    height=512
)
generated_image = text2image_converter.generate_image(text_params)
"""

@dataclass
class GenerationParameters:
    """Base parameters for image generation/transformation"""
    prompt: str = ""
    negative_prompt: str = ""
    strength: float = 0.5
    steps: int = 60
    
    def validate(self) -> None:
        """Validate common parameters"""
        if self.strength < 0.1 or self.strength > 1:
            raise ValueError("strength must be >0 and <1")
        if self.steps <= 0 or self.steps >= 100:
            raise ValueError("steps must be >0 and <100")

@dataclass
class Image2ImageParameters(GenerationParameters):
    """Parameters for image-to-image transformation"""
    input_image: Optional[Image.Image] = None
    mask_image: Optional[Image.Image] = None
    
    def validate(self) -> None:
        """Validate image-specific parameters"""
        super().validate()
        if self.input_image is None:
            raise ValueError("input_image is required")

    @classmethod
    def for_style_transfer(cls, image: Image.Image, style_prompt: str) -> "Image2ImageParameters":
        """Factory method for style transfer parameters"""
        return cls(
            input_image=image,
            prompt=style_prompt,
            strength=0.8,
            steps=50
        )

    @classmethod
    def for_inpainting(cls, image: Image.Image, mask: Image.Image, prompt: str) -> "Image2ImageParameters":
        """Factory method for inpainting parameters"""
        return cls(
            input_image=image,
            mask_image=mask,
            prompt=prompt,
            strength=1.0,
            steps=75
        )

@dataclass
class Text2ImageParameters(GenerationParameters):
    """Parameters for text-to-image generation"""
    width: int = 512
    height: int = 512
    
    def validate(self) -> None:
        """Validate text-to-image specific parameters"""
        super().validate()
        if not self.prompt:
            raise ValueError("prompt is required for text2image generation")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")

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