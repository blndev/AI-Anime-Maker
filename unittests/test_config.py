from configparser import ConfigParser
import random
import unittest
import sqlite3
import uuid

import sys
import os

# Übergeordnetes Verzeichnis zum Suchpfad hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import src.config as src_config

class TestConfiguration(unittest.TestCase):

    def setUp(self):
        """Setzt die Test-Datenbank auf."""
        # prepare configuration 
        src_config.current_config = ConfigParser()
        # we use random values for testing
        self.testconfiguration = {
            'General': {
                'app_title': "UNITTEST",
                'app_disclaimer': str(uuid.uuid4()),
                'user_message': str(uuid.uuid4()),
                'port': str(random.randint(2048, 32000)),
                'is_shared': random.choice([True, False]),
                'save_output': random.choice([True, False]),
                'output_folder': str(uuid.uuid4()),
                'cache_enabled': random.choice([True, False]),
                'cache_folder': str(uuid.uuid4()),
                'analytics_db_path': str(uuid.uuid4()),
                'analytics_enabled': random.choice([True, False]),
                'analytics_city_db': str(uuid.uuid4()),
            },
            'GenAI': {
                'default_model': str(uuid.uuid4()),
                'model_folder': str(uuid.uuid4()),
                'safetensor_url': str(uuid.uuid4()),
                'default_steps': random.randint(10, 100),
                'default_strength': random.uniform(0, 1),
                'max_size': random.randint(128, 4096),
            },
            'UI': {
                'show_steps': random.choice([True, False]),
                'show_strength': random.choice([True, False]),
                'theme': str(uuid.uuid4())
            },
            'Styles': {
                'style_count': random.randint(1, 10),
                'general_negative_prompt': str(uuid.uuid4())
            }
        }
        for i in range(1,self.testconfiguration["Styles"]["style_count"]):
            self.testconfiguration["Styles"][f"style_{i}_name"]=str(uuid.uuid4())
            self.testconfiguration["Styles"][f"style_{i}_prompt"]=str(uuid.uuid4())
            self.testconfiguration["Styles"][f"style_{i}_negative_prompt"]=str(uuid.uuid4())
            self.testconfiguration["Styles"][f"style_{i}_strength"]=random.uniform(0, 1)

    def tearDown(self):
        """nothing do now so far."""

    def test_general_settings(self):
        """Check section general."""
        src_config.current_config = ConfigParser()
        src_config.current_config.read_dict(self.testconfiguration)

        self.assertIsNotNone(src_config.current_config)  # Sicherstellen, dass ein Ergebnis zurückkommt
        general = self.testconfiguration["General"]
        self.assertEqual(src_config.get_app_title(), general["app_title"])  
        self.assertEqual(src_config.get_app_disclaimer(), general["app_disclaimer"],"disclaimer failed")  
        self.assertEqual(src_config.get_user_message(), general["user_message"])  
        
        self.assertEqual(src_config.get_server_port(), general["port"])  
        self.assertEqual(src_config.is_gradio_shared(), general["is_shared"])

        self.assertEqual(src_config.is_save_output_enabled(), general["save_output"])
        self.assertEqual(src_config.get_output_folder(), general["output_folder"])  

        self.assertEqual(src_config.is_cache_enabled(), general["cache_enabled"])  
        self.assertEqual(src_config.get_cache_folder(), general["cache_folder"])  

        self.assertEqual(src_config.is_analytics_enabled(), general["analytics_enabled"])  
        self.assertEqual(src_config.get_analytics_db_path(), general["analytics_db_path"])  
        self.assertEqual(src_config.get_analytics_city_db(), general["analytics_city_db"])  

    def test_general_defaults(self):
        """Check section general."""
        src_config.current_config = ConfigParser()
        src_config.current_config.read_dict({})
        self.assertIsNotNone(src_config.current_config)  # Sicherstellen, dass ein Ergebnis zurückkommt
        
        self.assertEqual(src_config.get_app_title(), "Funny Image Converter")  
        self.assertEqual(src_config.get_app_disclaimer(), "")  

        self.assertEqual(src_config.get_user_message(), "")  
        self.assertEqual(src_config.get_server_port(), None)  
        self.assertEqual(src_config.is_gradio_shared(), False)

        self.assertEqual(src_config.is_save_output_enabled(), False)
        self.assertEqual(src_config.get_output_folder(), "./output/")  

        self.assertEqual(src_config.is_cache_enabled(), False)  
        self.assertEqual(src_config.get_cache_folder(), "./cache/")  

        self.assertEqual(src_config.is_analytics_enabled(), False)  
        self.assertEqual(src_config.get_analytics_db_path(), "./analytics.db")  
        self.assertEqual(src_config.get_analytics_city_db(), "./GeoLite2-City.mmdb")  

    def test_UI_settings(self):
        """Check section UI."""
        src_config.current_config = ConfigParser()
        src_config.current_config.read_dict(self.testconfiguration)

        self.assertIsNotNone(src_config.current_config)  # Sicherstellen, dass ein Ergebnis zurückkommt
        section = self.testconfiguration["UI"]
        self.assertEqual(src_config.UI_show_stength_slider(), section["show_strength"])  
        self.assertEqual(src_config.UI_show_steps_slider(), section["show_steps"])  
        self.assertEqual(src_config.UI_get_gradio_theme(), section["theme"])  

    def test_UI_defaults(self):
        """Check section UI."""
        src_config.current_config = ConfigParser()
        src_config.current_config.read_dict({})
        self.assertIsNotNone(src_config.current_config)  # Sicherstellen, dass ein Ergebnis zurückkommt
        
        self.assertEqual(src_config.UI_show_stength_slider(), False)  
        self.assertEqual(src_config.UI_show_steps_slider(), False)  
        self.assertEqual(src_config.UI_get_gradio_theme(), "")  

    def test_AI_settings(self):
        """Check section UI."""
        src_config.current_config = ConfigParser()
        src_config.current_config.read_dict(self.testconfiguration)

        self.assertIsNotNone(src_config.current_config)  # Sicherstellen, dass ein Ergebnis zurückkommt
        section = self.testconfiguration["GenAI"]
        self.assertEqual(src_config.get_default_strength(), section["default_strength"])  
        self.assertEqual(src_config.get_default_steps(), section["default_steps"])  
        self.assertEqual(src_config.get_model(), section["default_model"])  
        self.assertEqual(src_config.get_model_folder(), section["model_folder"])  
        self.assertEqual(src_config.get_model_url(), section["safetensor_url"])  
        self.assertEqual(src_config.get_max_size(), section["max_size"])  

    def test_AI_settings_autocorrection(self):
        """Check section UI."""
        src_config.current_config = ConfigParser()

        src_config.current_config.read_dict({})
        default_steps = src_config.get_default_steps()
        default_strengths = src_config.get_default_strength()

        # set values which are to high
        src_config.current_config.read_dict(
            {'GenAI': {
                'default_steps': 500,
                'default_strengths': 2,
            }}
        )
        self.assertEqual(src_config.get_default_strength(), default_strengths)  
        self.assertEqual(src_config.get_default_steps(), default_steps)  

        # set values which are to low
        src_config.current_config.read_dict(
            {'GenAI': {
                'default_steps': 5,
                'default_strengths': 0,
            }}
        )
        self.assertEqual(src_config.get_default_strength(), default_strengths)  
        self.assertEqual(src_config.get_default_steps(), default_steps)  

    def test_AI_defaults(self):
        """Check section UI."""
        src_config.current_config = ConfigParser()
        src_config.current_config.read_dict({})

        self.assertIsNotNone(src_config.current_config)  # Sicherstellen, dass ein Ergebnis zurückkommt
        section = self.testconfiguration["GenAI"]
        self.assertEqual(src_config.get_default_strength(), 0.5)  
        self.assertEqual(src_config.get_default_steps(), 50)  

        self.assertEqual(src_config.get_model(), "./models/toonify.safetensors")  
        self.assertEqual(src_config.get_model_folder(), "./models/")  
        self.assertEqual(src_config.get_model_url(), "https://civitai.com/api/download/models/244831?type=Model&format=SafeTensor&size=pruned&fp=fp16")  
        self.assertEqual(src_config.get_max_size(), 1024)  

    def test_Styles_settings(self):
        """Check section UI."""
        src_config.current_config = ConfigParser()
        src_config.current_config.read_dict(self.testconfiguration)

        self.assertIsNotNone(src_config.current_config)  # Sicherstellen, dass ein Ergebnis zurückkommt
        section = self.testconfiguration["Styles"]
        self.assertEqual(src_config.get_style_count(), section["style_count"])  
        self.assertEqual(src_config.get_general_negative_prompt(), section["general_negative_prompt"])

        for i in range(1,src_config.get_style_count()):
            self.assertEqual(src_config.get_style_name(i), section[f"style_{i}_name"])
            self.assertEqual(src_config.get_style_prompt(i), section[f"style_{i}_prompt"])
            self.assertEqual(src_config.get_style_negative_prompt(i), section["general_negative_prompt"] + "," + section[f"style_{i}_negative_prompt"])
            self.assertEqual(src_config.get_style_strengths(i), section[f"style_{i}_strength"])

        # not existing styles and defaults
        self.assertEqual(src_config.get_style_name(99), "Style 99")
        self.assertEqual(src_config.get_style_prompt(99), "")
        self.assertEqual(src_config.get_style_negative_prompt(99), section["general_negative_prompt"] + ",")
        self.assertEqual(src_config.get_style_strengths(99), self.testconfiguration["GenAI"]["default_strength"])

if __name__ == "__main__":
    unittest.main()
