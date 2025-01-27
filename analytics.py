import ipaddress
import gradio as gr
import sqlite3          # as datastore
import config           # to get configuration values
import geoip2.database  # for ip to city
import os               # to check if files exists
from threading import Lock  # write to DB must be thread save
from user_agents import parse as parse_user_agent   # Split OS. Browser etc.

# read only database for getting location from IP
_ip_geo_reader = None
DEBUG = False

def _load_geo_db():
    """loads the ip to city database if existing"""
    global _ip_geo_reader
    try:
        db = config.get_analytics_city_db()
        if not os.path.exists(db): return
        _ip_geo_reader = geoip2.database.Reader(db)
    except Exception as e:
        print ("Error while loading geo ip database", e)

def _create_tables():

    if DEBUG: print ("check or create analytics tables")
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

    # # Table for permanent Input Image - Bans 
    # create_table_blocked_source = """
    # CREATE TABLE IF NOT EXISTS tblBlockedSource (
    #     SHA1 TEXT NOT NULL PRIMARY KEY,
    #     Reason TEXT,
    #     Message TEXT
    # );
    # """

    try:
        lock = Lock()
        with lock:
            with sqlite3.connect(config.get_analytics_db_path()) as connection:
                cursor = connection.cursor()
                cursor.execute(create_table_generations)
                cursor.execute(create_table_session)
                #cursor.execute(create_table_blocked_source)
                connection.commit()
    except sqlite3.Error as e:
        print(f"Error while creating tables: {e}")

def _write_thread_save_to_db(query, data):
    """as we running multi threaded we need to avoid conflicts on the database"""
    # for bigger scaling usage suggestion is to use a dedicated database system
    if DEBUG: print("write to db", query, data)
    try:
        lock = Lock()
        with lock:
            with sqlite3.connect(config.get_analytics_db_path()) as connection:
                cursor = connection.cursor()
                cursor.execute(query, data)
                connection.commit()
    except sqlite3.Error as e:
        print(f"Error while save session info {e}")

def start():
    """this will open or create the database if analytics is enable"""
    global _connection
    if not config.is_analytics_enabled: return
    try:
        print("check analytics database...", end="")
        _create_tables()
        _load_geo_db()
        print("ready")
    except Exception as e:
        print (e)


def stop():
    if _ip_geo_reader!=None:
        if DEBUG: print("closing analytics database")
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
            if DEBUG: print("split languages failed", e)
    
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
            if DEBUG: print("failed to determine country and city", e)

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
