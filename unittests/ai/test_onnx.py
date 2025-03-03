import unittest
from PIL import Image, ImageDraw, ImageFont
import sys
import os

# Übergeordnetes Verzeichnis zum Suchpfad hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from .testimages import images_by_group
import src.config as config

@unittest.skipIf(config.SKIP_ONNX, "Skipping ONNX Model tests")
class Test_ONNX(unittest.TestCase):

    import src.detectors.FaceAnalyzer as src_onnx
    images = images_by_group

    @classmethod
    def setUpClass(cls):
        config.read_configuration()
        cls.img_no_face = Image.new("RGB", (256, 256), color="blue")
        cls.FaceAnalyzer = cls.src_onnx.FaceAnalyzer()

    @classmethod
    def tearDownClass(cls):
        """cleanup test environment."""
        print("tear down class")
        if cls.FaceAnalyzer:
            del cls.FaceAnalyzer

    def setUp(self):
        """before each test case"""
        pass

    def tearDown(self):
        """after each test case."""
        pass

    def test_has_no_face(self):
        """check that the image has a face"""
        v = self.FaceAnalyzer.get_gender_and_age_from_image(self.img_no_face)
        self.assertEqual(len(v), 0)

    def test_is_gender(self):
        """check that the image has the correct gender and there are no false positives"""
        for gender in self.images:
            for age in self.images[gender]:
                for expression in self.images[gender][age]:
                    id = f"{gender}, age {age}, {expression}"
                    image = self.images[gender][age][expression]
                    v = self.FaceAnalyzer.get_gender_and_age_from_image(image)
                    self.assertNotEqual(len(v), 0, f"No face deteted on {id}")
                    if gender=="male":
                        self.assertTrue(v[0]["isMale"], id)
                        self.assertFalse(v[0]["isFemale"], id)
                    else:
                        self.assertFalse(v[0]["isMale"], id)
                        self.assertTrue(v[0]["isFemale"], id)

    def test_age(self):
        """check that the image has the correct gender and there are no false positives"""
        for gender in self.images:
            for age in self.images[gender]:
                for expression in self.images[gender][age]:
                    id = f"{gender}, age {age}, {expression}"
                    image = self.images[gender][age][expression]
                    v = self.FaceAnalyzer.get_gender_and_age_from_image(image)
                    self.assertNotEqual(len(v), 0, f"No face deteted on {id}")
                    self.assertLessEqual(v[0]["maxAge"], age+15, id)
                    self.assertLessEqual(age-10, v[0]["minAge"], id)

    def test_is_female(self):
        """check that all images which shoudl be female are female, ignore false posistives"""
        for gender in self.images:
            for age in self.images[gender]:
                for expression in self.images[gender][age]:
                    id = f"{gender}, age {age}, {expression}"
                    image = self.images[gender][age][expression]
                    v = self.FaceAnalyzer.get_gender_and_age_from_image(image)
                    self.assertNotEqual(len(v), 0, f"No face deteted on {id}")
                    if gender=="female":
                        self.assertFalse(v[0]["isMale"], id)
                        self.assertTrue(v[0]["isFemale"], id)

    def test_is_male(self):
        """check that all images which should be male are male, ignore false posistives"""
        for gender in self.images:
            for age in self.images[gender]:
                for expression in self.images[gender][age]:
                    id = f"{gender}, age {age}, {expression}"
                    image = self.images[gender][age][expression]
                    v = self.FaceAnalyzer.get_gender_and_age_from_image(image)
                    self.assertNotEqual(len(v), 0, f"No face deteted on {id}")
                    if gender=="male":
                        self.assertTrue(v[0]["isMale"], id)
                        self.assertFalse(v[0]["isFemale"], id)