from configparser import ConfigParser
import random
import unittest
import uuid

import sys
import os

# Übergeordnetes Verzeichnis zum Suchpfad hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.AI as src_AI
import src.config as config

#TODO Create a fake model class 

class TestAI(unittest.TestCase):

    def setUp(self):
        """."""
        # prepare configuration for use of in memory db and temp paths for output
        config.current_config = ConfigParser()
        self.db_path = f"./unittests/tmp/" + str(uuid.uuid4())
        config.current_config.read_dict({
            'General': {
                'analytics_db_path': self.db_path,
                'analytics_enabled': 'true',
                'analytics_city_db': './GeoLite2-City.mmdb',
            }
        })

        # mock of img2text pipeline which always retruns "ok"
        def captioner(image):
            v = []
            d = {'generated_text': "ok"}
            v.append(d)
            return v
        # mock of image loading pipeline
        def load_captioner_model():
            return captioner
        
        # assign mockups
        src_AI.IMAGE_TO_TEXT_PIPELINE = captioner
        src_AI._load_captioner_model = load_captioner_model


    def tearDown(self):
        """Remove Database file."""

        #TOD
    def test_caption_image(self):
        """Check if data is correctly stored into database."""
        # TODO make tmp image
        session = str(uuid.uuid4())
        value = src_AI.describe_image(None)#image)
        self.assertIsNotNone(value)  # Sicherstellen, dass ein Ergebnis zurückkommt
        self.assertEqual(value, "ok")  
 

if __name__ == "__main__":
    unittest.main()
