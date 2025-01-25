from configparser import ConfigParser
import random
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
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/12.10240"
        languages = "fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5"

        src_analytics.save_session(session=session, ip=ip, user_agent=user_agent, languages=languages)

        # read back the values
        self.cursor.execute(
            """SELECT
              session,
              OS, Browser, IsMobile,
              Language, UserAgent,
              Continent, Country, City
              FROM tblSessions WHERE session = ?""", (session,))

        result = self.cursor.fetchone()
        self.assertIsNotNone(result)  # Sicherstellen, dass ein Ergebnis zurückkommt
        self.assertEqual(result[0], session)  
        self.assertEqual(result[1], "Windows")  
        self.assertEqual(result[2], "Edge") 
        self.assertEqual(result[3], 0) 
        self.assertEqual(result[4], "fr-CH")  
        self.assertEqual(result[5], user_agent)  

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
              City
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
              City
              FROM tblSessions WHERE session = ?""", (session,))

        result = self.cursor.fetchone()
        self.assertIsNotNone(result) 
        self.assertEqual(result[0], session)  
        self.assertEqual(result[1], "Europe")  
        self.assertEqual(result[2], "United Kingdom")  
        self.assertEqual(result[3], "Neasden")  

    def test_save_generation(self):
        """Check if generation data is correctly stored into database."""
        
        #create 10 entries to check 
        for i in range(1,10):
            session = str(uuid.uuid4())
            sha1 = str(uuid.uuid4())
            style = str(uuid.uuid4())
            prompt = str(uuid.uuid4())
            ofn = str(uuid.uuid4())
            isBlocked = random.choice([True, False])
            br = str(uuid.uuid4())

            src_analytics.save_generation_details(
                session=session,
                sha1=sha1,
                style=style,
                prompt=prompt,
                output_filename=ofn,
                isBlocked=isBlocked,
                block_reason=br)


            self.cursor.execute(
                """SELECT
                Session,
                Input_SHA1,
                Style,
                Userprompt,
                Output,
                IsBlocked,
                BlockReason
                FROM tblGenerations WHERE session = ?""", (session,))

            result = self.cursor.fetchone()
            self.assertIsNotNone(result) 
            self.assertEqual(result[0], session)  
            self.assertEqual(result[1], sha1)  
            self.assertEqual(result[2], style)  
            self.assertEqual(result[3], prompt)  
            self.assertEqual(result[4], ofn)  
            self.assertEqual(result[5], isBlocked)  
            self.assertEqual(result[6], br)  

if __name__ == "__main__":
    unittest.main()
