from configparser import ConfigParser
import unittest
import sqlite3
import uuid

import sys
import os

# Übergeordnetes Verzeichnis zum Suchpfad hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import analytics as src_analytics
import config

class TestAnalytics(unittest.TestCase):

    def setUp(self):
        """Setzt die Test-Datenbank auf."""
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
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        src_analytics.start()


    def tearDown(self):
        """Remove Database file."""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        #TOD
    def test_save_session_user_agent(self):
        """Check if data is correctly stored into database."""
        # Beispielwert
        session = str(uuid.uuid4())
        ip = "1.1.1.1"
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240"
        languages = "EN-US" #todo use accept langaues string

        src_analytics.save_session(session=session, ip=ip, user_agent=user_agent, languages=languages)

        # read back the values
        self.cursor.execute(
            """SELECT
              session,
              Continent,
              Country,
              City,
              Client,
              Languages 
              FROM tblSessions WHERE session = ?""", (session,))

        result = self.cursor.fetchone()
        self.assertIsNotNone(result)  # Sicherstellen, dass ein Ergebnis zurückkommt
        self.assertEqual(result[0], session)  
        self.assertEqual(result[4], user_agent)  
        self.assertEqual(result[5], languages)  

    def test_save_session_private_ip(self):
        """Check if data is correctly stored into database."""
        # Beispielwert
        session = str(uuid.uuid4())
        ip = "192.168.0.1"
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240"
        languages = "EN-US" #todo use accept langaues string

        src_analytics.save_session(session=session, ip=ip, user_agent=user_agent, languages=languages)

        self.cursor.execute(
            """SELECT
              session,
              Continent,
              Country,
              City,
              Client,
              Languages 
              FROM tblSessions WHERE session = ?""", (session,))

        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], session)  
        self.assertEqual(result[1], "n.a.")  
        self.assertEqual(result[2], "n.a.")  
        self.assertEqual(result[3], "private IP")  

    def test_save_session_public_ip(self):
        """Check if data is correctly stored into database."""
        # Beispielwert
        session = str(uuid.uuid4())
        ip = "95.85.75.63"
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240"
        languages = "EN-US" #todo use accept langaues string

        src_analytics.save_session(session=session, ip=ip, user_agent=user_agent, languages=languages)

        self.cursor.execute(
            """SELECT
              session,
              Continent,
              Country,
              City,
              Client,
              Languages 
              FROM tblSessions WHERE session = ?""", (session,))

        result = self.cursor.fetchone()
        self.assertIsNotNone(result) 
        self.assertEqual(result[0], session)  
        self.assertEqual(result[1], "Europe")  
        self.assertEqual(result[2], "United Kingdom")  
        self.assertEqual(result[3], "Neasden")  


if __name__ == "__main__":
    unittest.main()
