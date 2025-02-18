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
    WITH SessionInputs AS (
        -- Get input data per session
        SELECT 
            i.Session,
            COUNT(*) as ImageUploads,
            GROUP_CONCAT(i.CachePath) as CachePaths
        FROM tblInput i
        GROUP BY i.Session
    ),
    SessionGenerations AS (
        -- Get all generations per session
        SELECT 
            g.session,
            COUNT(DISTINCT g.Id) as GenerationCount
        FROM tblGenerations g
        GROUP BY g.session
    )
    SELECT 
        s.*,
        date(s.Timestamp) as Date,
        COALESCE(si.ImageUploads, 0) as ImageUploads,
        COALESCE(sg.GenerationCount, 0) as GenerationCount,
        CASE 
            WHEN si.ImageUploads > 0 OR sg.GenerationCount > 0 THEN 1
            ELSE 0
        END as HasStartedGeneration,
        si.CachePaths
    FROM tblSessions s
    LEFT JOIN SessionInputs si ON si.Session = s.Session
    LEFT JOIN SessionGenerations sg ON sg.session = s.Session
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

def get_top_uploaded_images(df):
    """Get top 10 most frequently uploaded images with their details.
    
    Args:
        df: DataFrame containing session data with CachePaths column
    """
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    # Get all session IDs from the filtered DataFrame
    sessions = df['Session'].tolist()
    sessions_str = ','.join(f"'{s}'" for s in sessions)
    
    query = f"""
    WITH ImageUploads AS (
        -- Count uploads per unique SHA1
        SELECT 
            i.SHA1,
            COUNT(*) as UploadCount,
            -- Get details from first upload of this image
            MIN(i.ID) as ID,
            MIN(i.CachePath) as CachePath,
            MIN(i.Token) as Token,
            MIN(i.Face) as Face,
            MIN(i.Gender) as Gender,
            MIN(i.MinAge) as MinAge,
            MIN(i.MaxAge) as MaxAge,
            MIN(i.Timestamp) as UploadTime
        FROM tblInput i
        WHERE i.Session IN ({sessions_str})
        GROUP BY i.SHA1
        HAVING UploadCount > 1
        ORDER BY UploadCount DESC
        LIMIT 10
    )
    SELECT 
        SHA1,
        ID,
        CachePath,
        Token,
        Face,
        Gender,
        MinAge,
        MaxAge,
        UploadTime,
        UploadCount
    FROM ImageUploads
    """
    
    top_images = pd.read_sql_query(query, connection)
    connection.close()
    
    logger.info(f"Top uploaded images data loaded: {len(top_images)} rows")
    
    return top_images

def get_style_usage(df, start_date=None, end_date=None):
    """Get aggregated counts of generation styles used with percentages.
    
    Args:
        df: DataFrame containing session data with CachePaths column
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    """
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    # Get all session IDs from the filtered DataFrame
    sessions = df['Session'].tolist()
    sessions_str = ','.join(f"'{s}'" for s in sessions)
    
    # Build date filter condition
    date_filter = "AND date(g.Timestamp) BETWEEN ? AND ?" if start_date and end_date else ""
    date_params = [start_date, end_date] if start_date and end_date else []
    
    query = f"""
    WITH TotalCount AS (
        SELECT COUNT(*) as Total
        FROM tblGenerations g
        WHERE g.Session IN ({sessions_str})
        {date_filter}
    )
    SELECT 
        Style,
        COUNT(*) as Count,
        ROUND(CAST(COUNT(*) AS FLOAT) * 100 / Total, 1) as Percentage
    FROM tblGenerations g, TotalCount
    WHERE g.Session IN ({sessions_str})
    {date_filter}
    GROUP BY Style
    ORDER BY Count DESC
    """
    
    # Double the date parameters since we use them twice in the query
    params = date_params + date_params
    style_usage = pd.read_sql_query(query, connection, params=params)
    connection.close()
    
    logger.info(f"Style usage data loaded: {len(style_usage)} styles")
    
    return style_usage

def get_top_generated_images(df):
    """Get top 10 images that were used most for generations.
    
    Args:
        df: DataFrame containing session data with CachePaths column
    """
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    # Get all session IDs from the filtered DataFrame
    sessions = df['Session'].tolist()
    sessions_str = ','.join(f"'{s}'" for s in sessions)
    
    query = f"""
    WITH ImageGenerations AS (
        -- Count generations per unique SHA1
        SELECT 
            i.SHA1,
            COUNT(DISTINCT g.Id) as GenerationCount,
            -- Get details from first upload of this image
            MIN(i.ID) as ID,
            MIN(i.CachePath) as CachePath,
            MIN(i.Token) as Token,
            MIN(i.Face) as Face,
            MIN(i.Gender) as Gender,
            MIN(i.MinAge) as MinAge,
            MIN(i.MaxAge) as MaxAge,
            MIN(i.Timestamp) as UploadTime
        FROM tblInput i
        INNER JOIN tblGenerations g ON g.input_SHA1 = i.SHA1
        WHERE i.Session IN ({sessions_str})
        GROUP BY i.SHA1
        HAVING GenerationCount > 0
        ORDER BY GenerationCount DESC
        LIMIT 10
    )
    SELECT 
        SHA1,
        ID,
        CachePath,
        Token,
        Face,
        Gender,
        MinAge,
        MaxAge,
        UploadTime,
        GenerationCount
    FROM ImageGenerations
    """
    
    top_images = pd.read_sql_query(query, connection)
    connection.close()
    
    logger.info(f"Top generated images data loaded: {len(top_images)} rows")
    
    return top_images
