from configparser import ConfigParser
import random
import unittest
import uuid
from PIL import Image, ImageDraw, ImageFont
import sys
import os

# Übergeordnetes Verzeichnis zum Suchpfad hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.config as config
import src.utils as src_utils

class TestToken(unittest.TestCase):

    def setUp(self):
        """Setzt die Test-Datenbank auf."""
        # prepare configuration for use of in memory db and temp paths for output
        # config.current_config = ConfigParser()
        # self.db_path = f"./unittests/tmp/" + str(uuid.uuid4())
        # config.current_config.read_dict({
        #     'General': {
        #         'analytics_db_path': self.db_path,
        #         'analytics_enabled': 'true',
        #         'analytics_city_db': './GeoLite2-City.mmdb',
        #     }
        # })

        self.img_no_face = Image.new("RGB", (256, 256), color="blue") 
        #self.img_face = Image.open("./unittests/testdata/face.png")
        self.img_face = Image.open("https://user-images.githubusercontent.com/64628244/81032727-8381d880-8eae-11ea-84a2-34380601088c.png")


    def tearDown(self):
        """Remove Database file."""

    def test_has_face(self):
        """check that the image has a face"""

        v = src_utils.get_gender_and_age_from_image(self.img_face)
        self.assertIsNotNone(v)

    def test_has_no_face(self):
        """check that the image has a face"""

        v = src_utils.get_gender_and_age_from_image(self.img_no_face)
        self.assertEqual(len(v),0)
