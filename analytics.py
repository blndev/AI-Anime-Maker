# Features provided by this file
# * statistics about used styles and assoziated prompts
# * if store output and analytics are activated, prompts used for the generated output are stored
# * if cache, store output and analytics are activated, input and resulting images are connected 

import gradio as gr
import sqlite3          # as datastore
import config           # to get configuration values
import geoip2.database  # for ip to city
import os               # to check if files exists

_connection = None
_ip_geo_reader = None

def _create_tables(connection):

    #every user creates a session, even if he is not creating any content
    create_table_session = """
    CREATE TABLE IF NOT EXISTS tblSessions (
        Session TEXT NOT NULL PRIMARY KEY,
        Timestamp TEXT NOT NULL,
        IP TEXT,
        Continent TEXT,
        Country TEXT,
        City TEXT,
        Client TEXT,
        Languages TEXT
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
        cursor = connection.cursor()
        cursor.execute(create_table_generations)
        cursor.execute(create_table_session)
        #cursor.execute(create_table_blocked_source)
        connection.commit()
    except sqlite3.Error as e:
        print(f"Error while creating tables: {e}")

def _load_geo_db():
    """loads the ip to city database if existing"""
    global _ip_geo_reader
    try:
        db = config.get_analytics_city_db()
        if not os.path.exists(db): return
        _ip_geo_reader = geoip2.database.Reader(db)
    except Exception as e:
        print ("Error while loading geo ip database", e)

def start():
    """this will open or create the database if analytics is enable"""
    global _connection
    if not config.is_analytics_enabled: return
    try:
        print("Open analytics database")
        _connection = sqlite3.connect(config.get_analytics_db_path())
        _create_tables(_connection)
        _load_geo_db()
    except Exception as e:
        print (e)


def stop():
    if _connection!=None:
        print("closing analytics database")
        _connection.close()

def save_session(session, ip, client, languages):
    """creates an entry for the current user session if not existing"""

    #std query
    query = "insert or ignore into tblSessions (Session, Timestamp, IP, Client, Languages) values (?,datetime('now'),?,?,?)"
    data = (session, ip, client, languages)

    if _ip_geo_reader != None:
        try:
            ipinfo = _ip_geo_reader.city(ip)
            query = "insert or ignore into tblSessions (Session, Timestamp, IP, Client, Languages, Continent, Country, City) values (?,datetime('now'),?,?,?,?,?,?)"
            data = (session, ip, client, languages, 
                    ipinfo.continent.name, 
                    ipinfo.country.name,
                    ipinfo.city.name)
        except Exception as e:
            print("failed to determine country and city")
    print (query, data)
    try:
        if _connection == None: start()
        cursor = _connection.cursor()
        cursor.execute(query, data)
        _connection.commit()
    except sqlite3.Error as e:
        print(f"Error while save session info {e}")


# Simple Debug code
if __name__ == "__main__":
    start()
    save_session("3334", "95.99.246.145", "client", "de")
    cursor = _connection.cursor()
    cursor.execute("select * from tblSessions")
    rows = cursor.fetchall()
    for row in rows:
        print (row)