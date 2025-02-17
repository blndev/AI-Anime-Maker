import ipaddress
import sqlite3          # as datastore
import logging
import src.config as config           # to get configuration values
import geoip2.database  # for ip to city
import os               # to check if files exists
from threading import Lock  # write to DB must be thread save
from user_agents import parse as parse_user_agent   # Split OS. Browser etc.

# Set up module logger
logger = logging.getLogger(__name__)

# read only database for getting location from IP
_ip_geo_reader = None

def _load_geo_db():
    """loads the ip to city database if existing"""
    global _ip_geo_reader
    try:
        db = config.get_analytics_city_db()
        if not os.path.exists(db): return
        _ip_geo_reader = geoip2.database.Reader(db)
    except Exception as e:
        logger.error("Error while loading geo ip database: %s", str(e))
        logger.debug("Exception details:", exc_info=True)

def _create_tables():

    logger.debug("Checking or creating analytics tables")
    #every user creates a session, even if he is not creating any content
    create_table_session = """
    CREATE TABLE IF NOT EXISTS tblSessions (
        Session TEXT NOT NULL PRIMARY KEY,
        Timestamp TEXT NOT NULL,
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
        Timestamp TEXT NOT NULL,
        Session TEXT NOT NULL,
        Input_SHA1 TEXT NOT NULL,
        Style TEXT,
        Userprompt TEXT,
        Output TEXT,
        IsBlocked INTEGER,
        BlockReason TEXT,
        FOREIGN KEY(Session) REFERENCES tblSessions(Session)
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
        Token TEXT
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
    except sqlite3.Error as e:
        logger.error("Error while creating tables: %s", str(e))
        logger.debug("Exception details:", exc_info=True)

def _write_thread_save_to_db(query, data):
    """as we running multi threaded we need to avoid conflicts on the database"""
    # for bigger scaling usage suggestion is to use a dedicated database system
    logger.debug("Writing to db - Query: %s, Data: %s", query, data)
    try:
        lock = Lock()
        with lock:
            with sqlite3.connect(config.get_analytics_db_path()) as connection:
                cursor = connection.cursor()
                cursor.execute(query, data)
                connection.commit()
    except sqlite3.Error as e:
        logger.error("Error while saving session info: %s", str(e))
        logger.debug("Exception details:", exc_info=True)

def start():
    """this will open or create the database if analytics is enable"""
    global _connection
    if not config.is_analytics_enabled: return
    try:
        logger.info("Checking analytics database...")
        _create_tables()
        _load_geo_db()
        logger.info("Analytics database ready")
    except Exception as e:
        logger.error("Error during analytics startup: %s", str(e))
        logger.debug("Exception details:", exc_info=True)


def stop():
    if _ip_geo_reader!=None:
        logger.debug("Closing analytics database")
        _ip_geo_reader.close()

def save_session(session, ip, user_agent, languages):
    """creates an entry for the current user session if not existing"""
    if not config.is_analytics_enabled: return
    if languages!=None: 
        # get primary language only
        try:
            languages = languages.split(',')
            languages = languages[0].split(";")[0].strip()
        except Exception as e:
            logger.debug("Failed to split languages: %s", str(e))
            logger.debug("Exception details:", exc_info=True)
    
    continent = "n.a."
    country = "n.a."
    city = "private IP" if  ipaddress.ip_address(ip).is_private else "n.a."
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

    query = """
    insert or ignore into tblSessions 
    (Timestamp, Session, 
    OS, Browser, IsMobile,
    Language, UserAgent,
    Continent, Country, City)
    values (
        datetime('now'),?,
        ?,?,?,
        ?,?,
        ?,?,?)
    """
    ua = parse_user_agent(user_agent)
    isMobile = 1 if ua.is_mobile or ua.is_tablet else 0
    data = (session,
            ua.os.family, ua.browser.family, isMobile, 
            languages, user_agent,  
            continent, country, city)
# save all data now
    _write_thread_save_to_db(query, data)

def save_generation_details(session, sha1, style, prompt, output_filename, isBlocked=0, block_reason=None):
    """creates an entry for the current user session if not existing"""
    if not config.is_analytics_enabled: return
 
    #std query
    query = "insert or ignore into tblGenerations (Session, Timestamp, Input_SHA1, Style, Userprompt, Output,IsBlocked,BlockReason) values (?,datetime('now'),?,?,?,?,?,?)"
    data = (session, sha1, style, prompt, output_filename, isBlocked, block_reason)

    # save all data now
    _write_thread_save_to_db(query, data)

def save_input_image_details(session, sha1, cache_path_and_filename=None, face_detected: bool=False, gender: int=0, min_age=None, max_age=None, token=None):
    # db_path: Pfad zur SQLite-Datenbankdatei

    # Erstellen eines Datenobjekts (Dictionary), das die Parameter enthält
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
    INSERT OR IGNORE INTO tblInput (Timestamp, Session, SHA1, CachePath, Face, Gender, MinAge, MaxAge, Token)
    VALUES (CURRENT_TIMESTAMP, :Session, :SHA1, :CachePath, :Face, :Gender, :MinAge, :MaxAge, :Token)
    '''

    _write_thread_save_to_db(query=query, data=data)