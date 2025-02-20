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

class DataManager:
    def __init__(self):
        """Initialize DataManager with configuration and database connection."""
        logger.info("Initializing DataManager")
        try:
            config.read_configuration()
            self.db_path = config.get_analytics_db_path()
            logger.debug(f"Using database path: {self.db_path}")
            
            self.timezone = datetime.now().astimezone().tzinfo
            logger.debug(f"Using timezone: {self.timezone}")
            
            self._df = None  # Cache for the current filtered DataFrame
            self._city_coords = self._load_city_coordinates()  # Load city coordinates
            self._filters = {
                'continent': None,
                'country': None,
                'os': None,
                'browser': None,
                'language': None
            }
            logger.info("DataManager initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DataManager: {str(e)}")
            raise

    def _load_city_coordinates(self):
        """Load city coordinates from cities.csv."""
        try:
            cities_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cities.csv')
            if os.path.exists(cities_path):
                df = pd.read_csv(cities_path)
                city_coords = {}
                for _, row in df.iterrows():
                    if pd.notna(row['City']) and pd.notna(row['Country']):
                        # Create key with state if available
                        if pd.notna(row['State']):
                            key = f"{row['City']}, {row['State']}, {row['Country']}"
                        else:
                            key = f"{row['City']}, {row['Country']}"
                        city_coords[key] = (row['Longitude'], row['Latitude'])
                return city_coords
            else:
                logger.warning(f"Cities file not found at {cities_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading city coordinates: {e}")
            return {}

    def get_city_coordinates(self, city, country):
        """Get coordinates for a city, return (longitude, latitude, state) if found."""
        if not city or city == 'Unknown':
            return None
        
        # Try with just city and country
        key = f"{city}, {country}"
        coords = self._city_coords.get(key)
        if coords:
            return coords
        
        # Try all state variations for this city and country
        for full_key in self._city_coords.keys():
            if full_key.startswith(f"{city}, ") and full_key.endswith(f", {country}"):
                return self._city_coords[full_key]
        
        return None
    
    def add_filter(self, filter_type, value):
        """Add or update a filter."""
        if filter_type not in self._filters:
            raise ValueError(f"Invalid filter type: {filter_type}")
        self._filters[filter_type] = value
        
    def remove_filter(self, filter_type):
        """Remove a filter."""
        if filter_type not in self._filters:
            raise ValueError(f"Invalid filter type: {filter_type}")
        self._filters[filter_type] = None
        
    def reset_filters(self):
        """Reset all filters."""
        for key in self._filters:
            self._filters[key] = None
    
    def get_active_filters(self):
        """Get current active filters."""
        return {k: v for k, v in self._filters.items() if v is not None}
        
    def _get_connection(self):
        """Get a database connection."""
        try:
            logger.debug("Establishing database connection")
            conn = sqlite3.connect(self.db_path)
            logger.debug("Database connection established successfully")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def prepare_filtered_data(self, start_date=None, end_date=None, filters=None):
        """
        Main function to prepare filtered DataFrame based on global parameters.
        If filters is None, uses internal filter state.
        """
        logger.info(f"Preparing filtered data with date range: {start_date} to {end_date}")
        logger.debug(f"Applied filters: {filters if filters is not None else self._filters}")
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
        try:
            # Get base dataset
            df = self._get_session_data(start_date, end_date)
            
            # Use provided filters or internal filter state
            active_filters = filters if filters is not None else self._filters
            
            # Apply active filters
            if active_filters:
                initial_rows = len(df)
                if active_filters.get('continent'):
                    df = df[df['Continent'] == active_filters['continent']]
                if active_filters.get('country'):
                    df = df[df['Country'] == active_filters['country']]
                if active_filters.get('os'):
                    df = df[df['OS'] == active_filters['os']]
                if active_filters.get('browser'):
                    df = df[df['Browser'] == active_filters['browser']]
                if active_filters.get('language'):
                    df = df[df['Language'] == active_filters['language']]
                logger.debug(f"Filtered data from {initial_rows} to {len(df)} rows")
            
            # Cache the filtered DataFrame
            self._df = df
            logger.info(f"Successfully prepared filtered dataset with {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error preparing filtered data: {str(e)}")
            raise

    def _get_session_data(self, start_date=None, end_date=None):
        """Get base session data with all related information joined."""
        logger.debug(f"Fetching session data for date range: {start_date} to {end_date}")
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
        try:
            with self._get_connection() as conn:
                logger.debug("Executing session data query")
                df = pd.read_sql_query(query, conn, params=params)
                logger.debug(f"Retrieved {len(df)} session records")
            
            # Convert timestamps to local timezone
            df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize('GMT').dt.tz_convert(self.timezone)
            logger.info(f"Successfully retrieved and processed session data with {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error retrieving session data: {str(e)}")
            raise

    def get_top_uploaded_images(self):
        """Get top 10 most frequently uploaded images from current filtered dataset."""
        logger.debug("Fetching top uploaded images")
        if self._df is None:
            logger.error("No filtered dataset available")
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
        logger.debug("Fetching top generated images")
        if self._df is None:
            logger.error("No filtered dataset available")
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

    def get_image_by_id_or_sha1(self, search_value):
        """Get image details and its generations by input ID or SHA1."""
        logger.info(f"Searching for image with ID/SHA1: {search_value}")
        if not search_value:
            logger.debug("No search value provided")
            return None, pd.DataFrame()

        # Query to get image details - search in both ID and SHA1
        image_query = """
        SELECT 
            i.ID,
            i.SHA1,
            i.CachePath,
            i.Token,
            i.Face,
            i.Gender,
            i.MinAge,
            i.MaxAge,
            i.Timestamp
        FROM tblInput i
        WHERE i.ID = ? OR i.SHA1 = ?
        LIMIT 1
        """

        # Query to get all generations using this input
        generations_query = """
        SELECT 
            g.Id as GenerationId,
            g.Style,
            g.Userprompt as Prompt,
            g.Output as GeneratedImagePath,
            g.Timestamp
        FROM tblGenerations g
        WHERE g.Input_SHA1 = ?
        ORDER BY g.Timestamp DESC
        """

        try:
            with self._get_connection() as conn:
                # Try to parse as integer for ID search, use as string for SHA1
                try:
                    id_value = int(search_value)
                    logger.debug(f"Parsed search value as ID: {id_value}")
                except ValueError:
                    id_value = -1  # Invalid ID that won't match anything
                    logger.debug("Using search value as SHA1")
                
                # Get image details
                logger.debug("Querying image details")
                image_df = pd.read_sql_query(image_query, conn, params=[id_value, search_value])
                if len(image_df) == 0:
                    logger.info("No image found with provided ID/SHA1")
                    return None, pd.DataFrame()
                
                # Get generations using this image's SHA1
                logger.debug(f"Querying generations for SHA1: {image_df.iloc[0]['SHA1']}")
                generations_df = pd.read_sql_query(generations_query, conn, params=[image_df.iloc[0]['SHA1']])
                
                logger.info(f"Found image with {len(generations_df)} generations")
                return image_df.iloc[0], generations_df
        except Exception as e:
            logger.error(f"Database error in get_image_by_id_or_sha1: {str(e)}")
            return None, pd.DataFrame()

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

    def get_country_code_from_country(self, country, language=None):
        """Convert country name or language to ISO 3166-1 alpha-3 code."""
        country_code_map = {
            # Country mappings
            'United States': 'USA',
            'United Kingdom': 'GBR',
            'Germany': 'DEU',
            'France': 'FRA',
            'Italy': 'ITA',
            'Spain': 'ESP',
            'Canada': 'CAN',
            'Australia': 'AUS',
            'Japan': 'JPN',
            'China': 'CHN',
            'India': 'IND',
            'Brazil': 'BRA',
            'Russia': 'RUS',
            'South Korea': 'KOR',
            'Mexico': 'MEX',
            'Netherlands': 'NLD',
            'Sweden': 'SWE',
            'Switzerland': 'CHE',
            'Poland': 'POL',
            'Belgium': 'BEL',
            'Austria': 'AUT',
            'Norway': 'NOR',
            'Denmark': 'DNK',
            'Finland': 'FIN',
            'Singapore': 'SGP',
            'Ireland': 'IRL',
            'New Zealand': 'NZL',
            'Turkey': 'TUR',
        }
        
        language_country_map = {
            'en': 'USA',  # English -> United States
            'en-US': 'USA',
            'en-GB': 'GBR',
            'de': 'DEU',  # German -> Germany
            'de-DE': 'DEU',
            'de-AT': 'AUT',  # Austrian German
            'de-CH': 'CHE',  # Swiss German
            'fr': 'FRA',  # French -> France
            'fr-FR': 'FRA',
            'fr-CA': 'CAN',  # Canadian French
            'fr-BE': 'BEL',  # Belgian French
            'it': 'ITA',  # Italian -> Italy
            'es': 'ESP',  # Spanish -> Spain
            'es-ES': 'ESP',
            'es-MX': 'MEX',  # Mexican Spanish
            'ja': 'JPN',  # Japanese -> Japan
            'zh': 'CHN',  # Chinese -> China
            'zh-CN': 'CHN',
            'hi': 'IND',  # Hindi -> India
            'pt': 'BRA',  # Portuguese -> Brazil
            'pt-BR': 'BRA',
            'ru': 'RUS',  # Russian -> Russia
            'ko': 'KOR',  # Korean -> South Korea
            'nl': 'NLD',  # Dutch -> Netherlands
            'sv': 'SWE',  # Swedish -> Sweden
            'pl': 'POL',  # Polish -> Poland
            'no': 'NOR',  # Norwegian -> Norway
            'da': 'DNK',  # Danish -> Denmark
            'fi': 'FIN',  # Finnish -> Finland
            'tr': 'TUR',  # Turkish -> Turkey
        }
        
        # Try to get from country map first
        code = country_code_map.get(country)
        if code:
            return code
        else:
            logger.warning(f"Did not found a country-code for {country}")
            
        # If language is provided and no country match, try language map
        if language:
            code = language_country_map.get(language)
            if code:
                return code
            else:
                logger.warning(f"Did not found a country for language {language}")
            
        # Fallback to first 3 letters of country uppercase
        return country[:3].upper() if country else None

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
