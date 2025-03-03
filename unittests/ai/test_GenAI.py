import unittest
from unittest.mock import MagicMock
import uuid
from PIL import Image, ImageDraw, ImageFont

# Add parent Path to search path for python modules
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.config as config
import src.genai.AI as src_GenAI

#skip_genai = os.getenv("SKIP_GENAI") == "1"

@unittest.skipIf(os.getenv("SKIP_GPU") is not None, "Skipping GPU tests")
class Test_GenAI(unittest.TestCase):

    def setUp(self):
        """."""
        config.read_configuration()

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

    @unittest.skipIf(config.SKIP_AI, "Skipping GPU tests")
    def test_nsfw_detected(self):
        """Support function to check if the image is NSFW."""
        img = Image.new("RGB", (256, 256), color="pink")  # NSFW-Themed Background
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except:
            font = None
        draw.text((50, 100), "NSFW", fill="red", font=font)

        result_image, is_nsfw = src_GenAI.check_safety(img)
        self.assertFalse(is_nsfw)
        self.assertEqual(result_image, img)

    def test_describe_image_with_mocked_pipeline(self):
        """Check if data pipeline is correctly queried and pipeline text is returned."""
        # create tmp image
        srcImg = Image.new("L", (1024, 1024), 255)
        mockup_imageDescription = str(uuid.uuid4())

        def mock_image_to_text_pipeline(image):
            v = []
            d = {'generated_text': mockup_imageDescription}
            v.append(d)
            return v
        # mock of image loading pipeline

        def mockup_load_captioner_model():
            # we don't load an image to text model here, as this will blow
            # up build environment.
            return mock_image_to_text_pipeline

        # assign mockups
        src_GenAI.IMAGE_TO_TEXT_PIPELINE = mock_image_to_text_pipeline
        org_func = src_GenAI._load_captioner_model
        src_GenAI._load_captioner_model = mockup_load_captioner_model

        try:
            # execute the test
            value = src_GenAI.describe_image(srcImg)  # image)
            self.assertIsNotNone(value)
            self.assertEqual(value, mockup_imageDescription)
        finally:
            src_GenAI._load_captioner_model = org_func

    @unittest.skipIf(config.SKIP_AI, "Skipping GPU tests")
    def test_describe_image_with_vison_model(self):
        """Check if we get back data from describe image pipeline. The text can't be validated"""
        # create tmp image
        srcImg = Image.new("L", (1024, 1024), 255)

        # execute the test
        value = src_GenAI.describe_image(srcImg) 
        self.assertIsNotNone(value)
        self.assertNotEqual(value, "")
        print("generated description text", value)


    def test_change_text2img_model(self):
        """Check changing a model"""
        modelname = str(uuid.uuid4())

        def mockup_load_img2img_model(model="", use_cached_model=True):
            self.assertEqual(model, modelname)
            self.assertFalse(use_cached_model)
            return self.img2img_pipeline
        org_func = src_GenAI._load_img2img_model
        src_GenAI._load_img2img_model = mockup_load_img2img_model
        try:
            # execute test
            src_GenAI.change_text2img_model(modelname)
        finally:
            src_GenAI._load_img2img_model = org_func

    @unittest.skipIf(config.SKIP_AI, "Skipping GPU tests")
    def test_generate_image(self):
        """Check image generation"""
        # add a fake generator
        src_GenAI.IMAGE_TO_IMAGE_PIPELINE = self.img2img_pipeline
        img = Image.new("L", (config.get_max_size()*2, config.get_max_size()*2), 255)

        # execute test
        # self.assertRaises(src_AI.generate_image(image=None,prompt=""), "no image provided")
        result_image = src_GenAI.generate_image(
            image=img,
            prompt="create a image")
        self.assertIsNotNone(result_image)
        self.assertEqual(result_image.width, config.get_max_size(), "width wrong")
        self.assertEqual(result_image.width, config.get_max_size(), "height wrong")


if __name__ == "__main__":
    unittest.main()
