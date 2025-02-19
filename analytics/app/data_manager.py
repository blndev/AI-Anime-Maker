"""
DataManager class for analytics dashboard.
Centralizes all database operations and DataFrame management.
"""
import pandas as pd
import sqlite3
import logging
import os
import sys
from datetime import datetime
import pytz

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DataManager:
    def __init__(self):
        """Initialize DataManager with configuration and database connection."""
        config.read_configuration()
        self.db_path = config.get_analytics_db_path()
        self.timezone = datetime.now().astimezone().tzinfo
        self._df = None  # Cache for the current filtered DataFrame
        
    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def prepare_filtered_data(self, start_date=None, end_date=None, filters=None):
        """
        Main function to prepare filtered DataFrame based on global parameters.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            filters (dict): Dictionary containing filter values:
                - continent: Selected continent
                - country: Selected country
                - os: Selected operating system
                - browser: Selected browser
                - language: Selected language
        """
        # Get base dataset
        df = self._get_session_data(start_date, end_date)
        
        # Apply filters if provided
        if filters:
            if filters.get('continent'):
                df = df[df['Continent'] == filters['continent']]
            if filters.get('country'):
                df = df[df['Country'] == filters['country']]
            if filters.get('os'):
                df = df[df['OS'] == filters['os']]
            if filters.get('browser'):
                df = df[df['Browser'] == filters['browser']]
            if filters.get('language'):
                df = df[df['Language'] == filters['language']]
        
        # Cache the filtered DataFrame
        self._df = df
        return df

    def _get_session_data(self, start_date=None, end_date=None):
        """Get base session data with all related information joined."""
        query = """
        WITH SessionInputs AS (
            SELECT 
                i.Session,
                COUNT(*) as ImageUploads,
                GROUP_CONCAT(i.CachePath) as CachePaths
            FROM tblInput i
            GROUP BY i.Session
        ),
        SessionGenerations AS (
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
        
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        # Convert timestamps to local timezone
        df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize('GMT').dt.tz_convert(self.timezone)
        
        return df

    def get_top_uploaded_images(self):
        """Get top 10 most frequently uploaded images from current filtered dataset."""
        if self._df is None:
            raise ValueError("No filtered dataset available. Call prepare_filtered_data first.")
        
        sessions = self._df['Session'].tolist()
        sessions_str = ','.join(f"'{s}'" for s in sessions)
        
        query = f"""
        WITH ImageUploads AS (
            SELECT 
                i.SHA1,
                COUNT(*) as UploadCount,
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
        SELECT *
        FROM ImageUploads
        """
        
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            
            # If no results, return empty DataFrame with required columns
            if len(df) == 0:
                return pd.DataFrame(columns=[
                    'SHA1', 'GenerationCount', 'ID', 'CachePath',
                    'Token', 'Face', 'Gender', 'MinAge', 'MaxAge',
                    'UploadTime'
                ])
            return df

    def get_top_generated_images(self):
        """Get top 10 images used most for generations from current filtered dataset."""
        if self._df is None:
            raise ValueError("No filtered dataset available. Call prepare_filtered_data first.")
        
        sessions = self._df['Session'].tolist()
        sessions_str = ','.join(f"'{s}'" for s in sessions)
        
        query = f"""
        WITH ImageGenerations AS (
            SELECT 
                i.SHA1,
                COUNT(DISTINCT g.Id) as GenerationCount,
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
        SELECT *
        FROM ImageGenerations
        """
        
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)
            
            # If no results, return empty DataFrame with required columns
            if len(df) == 0:
                return pd.DataFrame(columns=[
                    'SHA1', 'GenerationCount', 'ID', 'CachePath',
                    'Token', 'Face', 'Gender', 'MinAge', 'MaxAge',
                    'UploadTime'
                ])
            return df

    def get_style_usage(self, start_date=None, end_date=None):
        """Get aggregated counts of generation styles used with percentages."""
        if self._df is None:
            raise ValueError("No filtered dataset available. Call prepare_filtered_data first.")
        
        sessions = self._df['Session'].tolist()
        sessions_str = ','.join(f"'{s}'" for s in sessions)
        
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
        
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=date_params * 2)
            
            # If no results, return empty DataFrame with required columns
            if len(df) == 0:
                return pd.DataFrame(columns=[
                    'Style', 'Count', 'Percentage'
                ])
            return df

    def get_filter_options(self):
        """Get available filter options from the current dataset."""
        if self._df is None:
            raise ValueError("No filtered dataset available. Call prepare_filtered_data first.")
            
        return {
            'continents': sorted(self._df['Continent'].unique().tolist()),
            'countries': sorted(self._df['Country'].unique().tolist()),
            'operating_systems': sorted(self._df['OS'].unique().tolist()),
            'browsers': sorted(self._df['Browser'].unique().tolist()),
            'languages': sorted(self._df['Language'].unique().tolist())
        }
