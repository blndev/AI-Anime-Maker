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

    @classmethod
    def setUpClass(cls):
        cls.captioner = ImageCaptioner()

    @classmethod
    def tearDownClass(cls):
        """cleanup test environment."""
        print("tear down class")
        if cls.captioner:
            cls.captioner.unload_pipeline()
            del cls.captioner
# 
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
        import threading

        img1 = Image.open("./unittests/testdata/face_female_age20_nosmile.jpg")
        img2 = Image.open("./unittests/testdata/face_male_age30_nosmile.jpg")
        img3 = Image.open("./unittests/testdata/face_female_age90_smile.jpg")

        results = [None, None, None]
        exceptions = [None, None, None]

        def run_describe_image(index, image):
            try:
                results[index] = self.captioner.describe_image(image)
            except Exception as e:
                exceptions[index] = e

        threads = [
            threading.Thread(target=run_describe_image, args=(0, img1)),
            threading.Thread(target=run_describe_image, args=(1, img2)),
            threading.Thread(target=run_describe_image, args=(2, img3))
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        for i in range(3):
            self.assertIsNone(exceptions[i], f"Thread {i} raised an exception: {exceptions[i]}")
            self.assertIsNot(results[i], "", f"Thread {i} returned an empty description")
