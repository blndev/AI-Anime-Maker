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
import src.utils.fileIO as fileIO
from unittests.testdata.testimages import images

# skip_genai = os.getenv("SKIP_GENAI") == "1"


@unittest.skipIf(os.getenv("SKIP_GPU") is not None, "Skipping GPU tests")
class Test_ConvertImage2ImageByStyle(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.AIPipeline = src_GenAI.ConvertImage2ImageByStyle(config.get_model())
        config.read_configuration()
        for descr, img in images.items():
            cls.single_image = img
            cls.single_image_descr = descr

    @classmethod
    def tearDownClass(cls):
        """cleanup test environment."""
        print("tear down class")
        if cls.AIPipeline:
            del cls.AIPipeline

    def test_generate_image(self):
        """Check image generation"""
        img = self.single_image
        descr = self.single_image_descr
        result_image = self.AIPipeline.generate_image(image=img, prompt=descr)
        self.assertIsNotNone(result_image)
        fileIO.save_image_as_file(result_image, "./testresults/")
        self.assertEqual(result_image.width, img.width, "width wrong")
        self.assertEqual(result_image.height, img.height, "height wrong")

    def test_generate_image_without_input_image(self):
        """Check image generation without input"""
        with self.assertRaises(ValueError):
            self.AIPipeline.generate_image(image=None, prompt="12345")

    def test_generate_image_without_prompt(self):
        """Check image generation without prompt"""
        img = self.single_image
        descr = self.single_image_descr
        result_image = self.AIPipeline.generate_image(image=img, prompt="")
        self.assertIsNotNone(result_image)
        fileIO.save_image_as_file(result_image, "./testresults/")
        self.assertEqual(result_image.width, img.width, "width wrong")
        self.assertEqual(result_image.height, img.height, "height wrong")

    def test_generate_image_strength_invalid(self):
        """Check image generation without prompt"""
        img = self.single_image
        descr = self.single_image_descr
        with self.assertRaises(ValueError):
            self.AIPipeline.generate_image(image=img, prompt=descr, strength=-1)
        with self.assertRaises(ValueError):
            self.AIPipeline.generate_image(image=img, prompt=descr, strength=2)

    def test_generate_image_steps_invalid(self):
        """Check image generation with invalid steps"""
        img = self.single_image
        descr = self.single_image_descr
        with self.assertRaises(ValueError):
            self.AIPipeline.generate_image(image=img, prompt=descr, steps=110)
        with self.assertRaises(ValueError):
            self.AIPipeline.generate_image(image=img, prompt=descr, steps=0)
