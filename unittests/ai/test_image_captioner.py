import unittest
import sys
import os
from unittest.mock import MagicMock
from PIL import Image

# Add parent Path to search path for python modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.genai import ImageCaptioner


@unittest.skipIf(os.getenv("SKIP_GPU") is not None, "Skipping GPU tests")
class Test_DescribeImage(unittest.TestCase):

    def setUp(self):
        self.captioner = ImageCaptioner()

    def tearDown(self):
        """cleanup test environment."""
        if self.captioner:
            self.captioner.unload_pipeline()
            del self.captioner

    def test_get_description(self):
        img = Image.open("./unittests/testdata/face_female_age20_nosmile.jpg")
        v = self.captioner.describe_image(img)
        self.assertIsNot(v, "", "no description, but description expected")
        self.assertIn("woman", v)

    def test_non_pil_image(self):
        img = bytearray()
        v = self.captioner.describe_image(img)
        self.assertIs(v, "", "empty description expected")
        # self.assertIn("woman", v)

    def test_empty_image(self):
        img = None
        v = self.captioner.describe_image(img)
        self.assertIs(v, "")
        # self.assertIn("woman", v)

    def test_singleton(self):
        c = ImageCaptioner()
        self.assertEqual(self.captioner, c, "there should be only one instance to save ressources")
        # self.assertIn("woman", v)

    def test_parallel_access(self):
        img1 = Image.open("./unittests/testdata/face_female_age20_nosmile.jpg")
        img2 = Image.open("./unittests/testdata/face_male_age30_nosmile.jpg")
        img3 = Image.open("./unittests/testdata/face_female_age90_smile.jpg")
        #implement 3 threads executing the captioner.describe_image at the same time
        # no error should occure, all functions shoould return an non empty result

