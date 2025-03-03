import ipaddress
import sqlite3          # as datastore
import logging
import src.config as config           # to get configuration values
import geoip2.database  # for ip to city
import os               # to check if files exists
from threading import Lock  # write to DB must be thread safe
from user_agents import parse as parse_user_agent   # Split OS. Browser etc.

# Set up module logger
logger = logging.getLogger(__name__)

# read only database for getting location from IP
_ip_geo_reader = None

def _load_geo_db():
    """loads the ip to city database if it exists"""
    global _ip_geo_reader
    try:
        db = config.get_analytics_city_db()
        if not os.path.exists(db): return
        _ip_geo_reader = geoip2.database.Reader(db)
    except Exception as e:
        logger.error("Error while loading geo ip database: %s", str(e))
        logger.debug("Exception details:", exc_info=True)

def _create_tables():
    """Creates the required tables in the analytics database if they don't exist."""
    logger.debug("Checking or creating analytics tables")
    #every user creates a session, even if he is not creating any content
    create_table_session = """
    CREATE TABLE IF NOT EXISTS tblSessions (
        Session TEXT NOT NULL PRIMARY KEY,
        Timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Continent TEXT,
        Country TEXT,
        City TEXT,
        OS TEXT,
        Browser TEXT,
        IsMobile INT,
        UserAgent TEXT,
        Language TEXT
    );
    """
    create_table_generations = """
    CREATE TABLE IF NOT EXISTS tblGenerations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Session TEXT NOT NULL,
        Input_SHA1 TEXT NOT NULL,
        Style TEXT,
        Userprompt TEXT,
        Output TEXT,
        IsBlocked INTEGER,
        BlockReason TEXT
    );
    """

    create_table_input = """
    CREATE TABLE IF NOT EXISTS tblInput (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Session TEXT NOT NULL,
        SHA1 TEXT NOT NULL,
        CachePath TEXT,
        Face BOOLEAN,
        Gender INTEGER,
        MinAge INTEGER,
        MaxAge INTEGER,
        Token INTEGER  NOT NULL
    );
    """

    try:
        lock = Lock()
        with lock:
            with sqlite3.connect(config.get_analytics_db_path()) as connection:
                cursor = connection.cursor()
                cursor.execute(create_table_session)
                cursor.execute(create_table_generations)
                cursor.execute(create_table_input)
                connection.commit()
                return True
    except sqlite3.Error as e:
        logger.error("Error while creating tables: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        return False

def _write_thread_safe_to_db(query: str, data: dict) -> bool:
    """Writes data to the database in a thread-safe manner.

    Args:
        query (str): The SQL query to execute
        data (dict): The data to insert/update

    Returns:
        bool: True if write was successful, False otherwise
    """
    logger.debug("Writing to db - Query: %s, Data: %s", query, data)
    try:
        lock = Lock()
        with lock:
            with sqlite3.connect(config.get_analytics_db_path()) as connection:
                cursor = connection.cursor()
                cursor.execute(query, data)
                connection.commit()
        return True
    except sqlite3.Error as e:
        logger.error("Error while saving to database: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        return False

def start() -> bool:
    """Initializes the analytics system.

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        logger.info("Checking analytics database...")
        if not _create_tables():
            return False
        _load_geo_db()
        logger.info("Analytics database ready")
        return True
    except Exception as e:
        logger.error("Error during analytics startup: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        return False

def stop():
    """Closes the analytics system cleanly."""
    if _ip_geo_reader!=None:
        logger.debug("Closing analytics database")
        _ip_geo_reader.close()

def save_session(session: str, ip: str, user_agent: str, languages: str = None) -> bool:
    """Creates an entry for the current user session if it doesn't exist.

    Args:
        session (str): The session identifier
        ip (str): The IP address of the user
        user_agent (str): The user agent string from the browser
        languages (str, optional): The language string from the browser. Defaults to None.

    Returns:
        bool: True if the session was saved successfully, False otherwise
    """
    if not config.is_analytics_enabled(): return True
    
    try:
        if languages!=None: 
            # get primary language only
            try:
                languages = languages.split(',')
                languages = languages[0].split(";")[0].strip()
            except Exception as e:
                logger.debug("Failed to split languages: %s", str(e))
                logger.debug("Exception details:", exc_info=True)
        
        continent = "n.a."
        country = "n.a." #TODO: get country by language as in dashboard for fallback and remove this logic from dashboard
        city = "private IP" if ipaddress.ip_address(ip).is_private else "n.a."
        if not ipaddress.ip_address(ip).is_private and _ip_geo_reader != None:
            try:
                ipinfo = _ip_geo_reader.city(ip)
                if ipinfo:
                    continent = ipinfo.continent.name
                    country = ipinfo.country.name
                    city = ipinfo.city.name
            except Exception as e:
                logger.debug("Failed to determine country and city: %s", str(e))
                logger.debug("Exception details:", exc_info=True)

        ua = parse_user_agent(user_agent)
        data = {
            'Session': session,
            'OS': ua.os.family,
            'Browser': ua.browser.family + (" (bot)" if ua.is_bot else ""),
            'IsMobile': 1 if ua.is_mobile or ua.is_tablet else 0,
            'Language': languages,
            'UserAgent': user_agent,
            'Continent': continent,
            'Country': country,
            'City': city
        }
        
        query = """
        INSERT OR IGNORE INTO tblSessions 
        (Timestamp, Session, OS, Browser, IsMobile, Language, UserAgent, Continent, Country, City)
        VALUES (
            datetime('now'), 
            :Session, :OS, :Browser, :IsMobile, :Language, :UserAgent, :Continent, :Country, :City
        )
        """
        
        return _write_thread_safe_to_db(query, data)
    except Exception as e:
        logger.error("Failed to save session: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        return False

def save_generation_details(session: str, sha1: str, style: str, prompt: str, 
                          output_filename: str, isBlocked: int = 0, 
                          block_reason: str = None) -> bool:
    """Creates an entry for an image generation attempt.

    Args:
        session (str): The session identifier
        sha1 (str): The SHA1 hash of the input image
        style (str): The style used for generation
        prompt (str): The user prompt/description
        output_filename (str): The filename of the generated image
        isBlocked (int, optional): Whether the generation was blocked. Defaults to 0.
        block_reason (str, optional): Reason for blocking if applicable. Defaults to None.

    Returns:
        bool: True if the generation details were saved successfully, False otherwise
    """
    if not config.is_analytics_enabled(): return True
    
    try:
        data = {
            'Session': session,
            'SHA1': sha1,
            'Style': style,
            'Prompt': prompt,
            'Output': output_filename,
            'IsBlocked': isBlocked,
            'BlockReason': block_reason
        }

        query = """
        INSERT OR IGNORE INTO tblGenerations 
        (Session, Timestamp, Input_SHA1, Style, Userprompt, Output, IsBlocked, BlockReason) 
        VALUES (
            :Session, datetime('now'), :SHA1, :Style, :Prompt, :Output, :IsBlocked, :BlockReason
        )
        """
        return _write_thread_safe_to_db(query, data)
    except Exception as e:
        logger.error("Failed to save generation details: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        return False

def save_input_image_details(session: str, sha1: str, cache_path_and_filename: str = None, 
                           face_detected: bool = False, gender: int = 0, 
                           min_age: int = None, max_age: int = None, 
                           token: int = 0) -> bool:
    """Saves details about an uploaded input image.

    Args:
        session (str): The session identifier
        sha1 (str): The SHA1 hash of the input image
        cache_path_and_filename (str, optional): Path where image is cached. Defaults to None.
        face_detected (bool, optional): Whether a face was detected. Defaults to False.
        gender (int, optional): Detected gender (0=unknown, 1=male, 2=female). Defaults to 0.
        min_age (int, optional): Minimum detected age. Defaults to None.
        max_age (int, optional): Maximum detected age. Defaults to None.
        token (str, optional): Associated token if any. Defaults to None.

    Returns:
        bool: True if the input details were saved successfully, False otherwise
    """
    if not config.is_analytics_enabled(): return True
    
    try:
        data = {
            'Session': session,
            'SHA1': sha1,
            'CachePath': cache_path_and_filename,
            'Face': 1 if face_detected else 0,
            'Gender': gender,
            'MinAge': min_age,
            'MaxAge': max_age,
            'Token': token
        }

        query = '''
        INSERT OR IGNORE INTO tblInput 
        (Timestamp, Session, SHA1, CachePath, Face, Gender, MinAge, MaxAge, Token)
        VALUES (CURRENT_TIMESTAMP, :Session, :SHA1, :CachePath, :Face, :Gender, :MinAge, :MaxAge, :Token)
        '''

        return _write_thread_safe_to_db(query=query, data=data)
    except Exception as e:
        logger.error("Failed to save input image details: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        return False
