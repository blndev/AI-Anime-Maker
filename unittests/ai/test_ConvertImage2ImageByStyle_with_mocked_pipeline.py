import unittest
from unittest.mock import MagicMock
import uuid
from PIL import Image, ImageDraw, ImageFont

# Add parent Path to search path for python modules
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.config as config
import src.genai as src_GenAI

#skip_genai = os.getenv("SKIP_GENAI") == "1"

@unittest.skipIf(os.getenv("SKIP_GPU") is not None, "Skipping GPU tests")
class Test_ConvertImage2ImageByStyle_with_mocked_pipeline(unittest.TestCase):

    def setUp(self):
        """."""
        config.read_configuration()

        self.AIPipeline = src_GenAI.ConvertImage2ImageByStyle(config.get_model())
        # mock image generation pipeline because generation itself is not testable
        def mock_img_to_img_pipeline(
                image: Image,
                mask_image: Image,
                prompt: str,
                negative_prompt: str = "",
                num_inference_steps=50,
                strength=0.0):
            img = Image.new("RGB", image.size, color="blue")
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.load_default()
            except:
                font = None
            draw.text((50, 100), "GENERATED", fill="yellow", font=font)
            o = MagicMock
            o.images = [img]
            return o
        self.img2img_pipeline = mock_img_to_img_pipeline

    def tearDown(self):
        """cleanup test environment."""

    def test_nsfw_detected(self):
        """Support function to check if the image is NSFW."""
        img = Image.new("RGB", (256, 256), color="pink")  # NSFW-Themed Background
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except:
            font = None
        draw.text((50, 100), "NSFW", fill="red", font=font)

        result_image, is_nsfw = self.AIPipeline.check_safety(img)
        self.assertFalse(is_nsfw)
        self.assertEqual(result_image, img)

    def test_change_text2img_model(self):
        """Check changing a model"""
        modelname = str(uuid.uuid4())

        def mockup_load_img2img_model(model="", use_cached_model=True):
            self.assertEqual(model, modelname)
            self.assertFalse(use_cached_model)
            return self.img2img_pipeline
        org_func = self.AIPipeline._load_img2img_model
        self.AIPipeline._load_img2img_model = mockup_load_img2img_model
        try:
            # execute test
            self.AIPipeline.change_img2img_model(modelname)
        finally:
            self.AIPipeline._load_img2img_model = org_func
