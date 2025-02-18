"""
Data access layer for analytics dashboard.
Handles all database interactions and DataFrame creation.
"""
import pandas as pd
import sqlite3
import logging
import os
import sys
from datetime import datetime
import pytz
"""
Data access layer for analytics dashboard.
Handles all database interactions and DataFrame creation.
"""

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_session_data(start_date=None, end_date=None, include_generation_status=False, include_input_data=False, timezone=None):
    """Get session data from analytics database with all related data joined.
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        include_generation_status (bool): Include whether session started generation
        include_input_data (bool): Include image upload counts
    """
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    # Build comprehensive query joining all tables
    query = """
    WITH InputGenerations AS (
        -- Get generations linked to inputs
        SELECT 
            i.Session,
            i.SHA1,
            COUNT(DISTINCT g.Id) as GenerationCount
        FROM tblInput i
        LEFT JOIN tblGenerations g ON g.input_SHA1 = i.SHA1
        GROUP BY i.Session, i.SHA1
    ),
    DirectGenerations AS (
        -- Get generations not linked to any input
        SELECT 
            s.Session,
            COUNT(DISTINCT g.Id) as GenerationCount
        FROM tblSessions s
        INNER JOIN tblGenerations g ON g.session = s.Session
        WHERE g.input_SHA1 NOT IN (SELECT SHA1 FROM tblInput)
        GROUP BY s.Session
    ),
    SessionInputs AS (
        -- Get input data and their generations per session
        SELECT 
            i.Session,
            COUNT(*) as ImageUploads,
            GROUP_CONCAT(i.CachePath) as CachePaths,
            SUM(COALESCE(ig.GenerationCount, 0)) as GenerationCount
        FROM tblInput i
        LEFT JOIN InputGenerations ig ON ig.Session = i.Session AND ig.SHA1 = i.SHA1
        GROUP BY i.Session
    )
    SELECT 
        s.*,
        date(s.Timestamp) as Date,
        COALESCE(si.ImageUploads, 0) as ImageUploads,
        COALESCE(si.GenerationCount, 0) + COALESCE(dg.GenerationCount, 0) as GenerationCount,
        CASE 
            WHEN si.ImageUploads > 0 OR si.GenerationCount > 0 OR dg.GenerationCount > 0 THEN 1
            ELSE 0
        END as HasStartedGeneration,
        si.CachePaths
    FROM tblSessions s
    LEFT JOIN SessionInputs si ON si.Session = s.Session
    LEFT JOIN DirectGenerations dg ON dg.Session = s.Session
    """
    
    if start_date and end_date:
        query += " WHERE date(s.Timestamp) BETWEEN ? AND ?"
    
    query += " ORDER BY s.Timestamp"
    
    params = [start_date, end_date] if start_date and end_date else []
    
    df = pd.read_sql_query(query, connection, params=params)
    connection.close()
    
    # Convert timestamps from GMT to local timezone
    if timezone is None:
        # Default to system timezone if none specified
        timezone = datetime.now().astimezone().tzinfo
    elif isinstance(timezone, str):
        timezone = pytz.timezone(timezone)
    
    # Convert Timestamp column from GMT to local time
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize('GMT').dt.tz_convert(timezone)
    
    # Log data loading info
    logger.info(f"Session data loaded: {len(df)} rows")
    if len(df) > 0:
        logger.debug(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        logger.debug(f"Sample dates: {df['Date'].head().tolist()}")
    
    return df

def get_top_images(df):
    """Get top 10 most frequently uploaded images from the session data.
    
    Args:
        df: DataFrame containing session data with CachePaths column
    """
    # Split CachePaths into rows (it's stored as comma-separated string)
    paths_df = df[df['CachePaths'].notna()].copy()
    paths_df['CachePath'] = paths_df['CachePaths'].str.split(',')
    paths_df = paths_df.explode('CachePath')
    
    # Count occurrences of each path
    top_images = paths_df['CachePath'].value_counts().head(10).reset_index()
    top_images.columns = ['CachePath', 'UploadCount']
    
    logger.info(f"Top images data loaded: {len(top_images)} rows")
    
    return top_images
