"""
Data access layer for analytics dashboard.
Handles all database interactions and DataFrame creation.
"""
import pandas as pd
import sqlite3
import logging
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_session_data(start_date=None, end_date=None, include_generation_status=False, include_input_data=False):
    """Get session data from analytics database.
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        include_generation_status (bool): Include whether session started generation
        include_input_data (bool): Include image upload counts
    """
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    # Handle datetime format YYYY-MM-DD HH:MM:SS
    base_query = """
    SELECT 
        s.*,
        date(s.Timestamp) as Date
    """
    
    if include_generation_status:
        base_query += """,
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM tblGenerations g WHERE g.Session = s.Session
                UNION
                SELECT 1 FROM tblInput i WHERE i.Session = s.Session
            ) THEN 1
            ELSE 0
        END as HasStartedGeneration
        """
    
    if include_input_data:
        base_query += """,
        (
            SELECT COUNT(*)
            FROM tblInput i
            WHERE i.Session = s.Session
        ) as ImageUploads
        """
    
    base_query += " FROM tblSessions s"
    
    if start_date and end_date:
        base_query += " WHERE date(s.Timestamp) BETWEEN ? AND ?"
    
    base_query += " ORDER BY s.Timestamp"
    
    query = base_query
    params = [start_date, end_date] if start_date and end_date else []
    
    df = pd.read_sql_query(query, connection, params=params)
    connection.close()
    
    # Log data loading info
    logger.info(f"Session data loaded: {len(df)} rows")
    if len(df) > 0:
        logger.debug(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        logger.debug(f"Sample dates: {df['Date'].head().tolist()}")
    
    return df

def get_top_images(start_date=None, end_date=None):
    """Get top 10 most frequently uploaded images with their paths.
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    """
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    query = """
    SELECT 
        i.SHA1,
        i.CachePath,
        COUNT(*) as UploadCount
    FROM tblInput i
    JOIN tblSessions s ON i.Session = s.Session
    """
    
    if start_date and end_date:
        query += " WHERE date(s.Timestamp) BETWEEN ? AND ?"
    
    query += """
    GROUP BY i.SHA1, i.CachePath
    ORDER BY UploadCount DESC
    LIMIT 10
    """
    
    params = [start_date, end_date] if start_date and end_date else []
    
    df = pd.read_sql_query(query, connection, params=params)
    connection.close()
    
    logger.info(f"Top images data loaded: {len(df)} rows")
    
    return df
