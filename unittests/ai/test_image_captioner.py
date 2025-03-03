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

# skip_genai = os.getenv("SKIP_GENAI") == "1"


@unittest.skipIf(os.getenv("SKIP_GPU") is not None, "Skipping GPU tests")
class Test_DescribeImage(unittest.TestCase):

    def setUp(self):
        self.AIPipeline = src_GenAI.ConvertImage2ImageByStyle()

    def tearDown(self):
        """cleanup test environment."""
        if self.AIPipeline:
            self.AIPipeline._cleanup_captioner()
            del self.AIPipeline

    def test_get_description(self):
        img = Image.open("./unittests/testdata/face_female_age20_nosmile.jpg")
        v = self.AIPipeline.describe_image(img)
        self.assertIsNot(v, "", "no description, but description expected")
        self.assertIn("woman", v)

    def test_non_pil_image(self):
        img = bytearray()
        v = self.AIPipeline.describe_image(img)
        self.assertIs(v, "", "empty description expected")
        #self.assertIn("woman", v)

    def test_empty_image(self):
        img = None
        v = self.AIPipeline.describe_image(img)
        self.assertIs(v, "")
        #self.assertIn("woman", v)
