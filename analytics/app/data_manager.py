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
from  iso3166 import countries as countrycodes

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
            # Add country codes using both country and language
            df['CountryCode'] = df.apply(
                lambda x: self.get_country_code_from_country(x['Country'], x['Language']),
                axis=1
            )
            #if we have no countty, we can use the determined country code based on the language
            df.loc[df['Country'] == "n.a.", "Country"] =  df['CountryCode'].apply(
                lambda cc: countrycodes.get(cc).name if countrycodes.get(cc) else "n.a."    
            )
            # translate now the ISO-Code to a country
            #df['Country'].apply(lambda country: iso3166.countries_by_alpha3.get(alpha3=country))
        
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
            try:
                df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize('GMT').dt.tz_convert(self.timezone)
            except TypeError:
                logger.debug("time zone conversion failed. potentially already tz aware")
            logger.info(f"Successfully retrieved and processed session data with {len(df)} records")
            return df
        except Exception as e:
            logger.debug(f"Error retrieving session data: {str(e)}")
            logger.error(f"Error retrieving session data. Empty or wrong database at {config.get_analytics_db_path()}\n\nAnalytics will be stopped.")
            sys.exit(1)

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
                MAX(i.Token) as Token,
                MAX(i.Face) as Face,
                MAX(i.Gender) as Gender,
                MIN(i.MinAge) as MinAge,
                MAX(i.MaxAge) as MaxAge,
                MIN(i.Timestamp) as UploadTime
            FROM tblInput i
            WHERE i.Session IN ({sessions_str})
            GROUP BY i.SHA1
            HAVING UploadCount > 0
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
                    'SHA1', 'UploadCount', 'ID', 'CachePath',
                    'Token', 'Face', 'Gender', 'MinAge', 'MaxAge',
                    'UploadTime'
                ])

            self._enhance_gender_age_face_data(df)
            return df

    _gender_to_text = {-1: "unkown", 0: "unkown", 1: "male", 2: "female", 3: "female + male"}
    def _enhance_gender_age_face_data(self, df):
        """ad readable information into the df"""
        df["Face"] = df["Face"].apply(lambda x: "yes" if x==1 else "no")
        df["GenderText"] = df["Gender"].apply(lambda x: self._gender_to_text[x])
        df["AgeSpan"] = df["MinAge"].astype(str) + " - " + df["MaxAge"].astype(str)
        return df

    def get_top_used_images(self):
        """Get top 10 images used most for generations from current filtered dataset."""
        logger.debug("Fetching top used images")
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
                MAX(i.Token) as Token,
                MAX(i.Face) as Face,
                MAX(i.Gender) as Gender,
                MIN(i.MinAge) as MinAge,
                MAX(i.MaxAge) as MaxAge,
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
            self._enhance_gender_age_face_data(df)
            return df

    def get_related_images(self, id: int=0, sha1:str =None):
        """Get top 10 images used most for generations from current filtered dataset."""
        # TODO anpassen, alles unten ist schon fast gut, nur das where muss anders
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
                MAX(i.Token) as Token,
                MAX(i.Face) as Face,
                MAX(i.Gender) as Gender,
                MIN(i.MinAge) as MinAge,
                MAX(i.MaxAge) as MaxAge,
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
            self._enhance_gender_age_face_data(df)
            return df

    def get_image_by_id_or_sha1(self, search_value):
        """Get image details and its generations by input ID or SHA1."""
        logger.info(f"Searching for image with ID/SHA1: {search_value}")
        if not search_value:
            logger.debug("No search value provided")
            return None, pd.DataFrame()

        # Query to get image details - search in both ID and SHA1
        image_query = f"""
        SELECT 
            *
        FROM tblInput
        WHERE ID = ? OR SHA1 = ?
        LIMIT 1
        """

        # Query to get all generations using this input
        sessions = self._df['Session'].tolist()
        sessions_str = ','.join(f"'{s}'" for s in sessions)
        ##sessionstr is used to apply the local set filters
        generations_query = f"""
        SELECT 
            (select count(*) from tblInput where SHA1 = ? and session in ({sessions_str})) as UploadCount,
            (select count(*) from tblGenerations where Input_SHA1 = ? and session in ({sessions_str}))as GenerationCount
        """

        try:
            with self._get_connection() as conn:
                
                # Get image details
                logger.debug("Querying image details")
                image_df = pd.read_sql_query(image_query, conn, params=[search_value, search_value])
                self._enhance_gender_age_face_data(image_df)
                if len(image_df) == 0:
                    logger.info("No image found with provided ID/SHA1")
                    return None, pd.DataFrame()
                
                # Get generations using this image's SHA1
                sha1=image_df.iloc[0]['SHA1'] 
                logger.debug(f"Querying generations for SHA1: {sha1}")
                generations_df = pd.read_sql_query(generations_query, conn, params=[sha1, sha1])
                
                logger.info(f"Found image with {len(generations_df)} generations")
                counter = generations_df.iloc[0]
                image_df["GenerationCount"] = counter["GenerationCount"]
                image_df["UploadCount"] = counter["UploadCount"]
                return image_df.iloc[0]
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

    def get_country_code_from_country(self, country=None, language=None):
        """Convert country name or language to ISO 3166-1 alpha-3 code."""
        for iso_country in countrycodes:
            if iso_country.name == country:
                logger.debug(f"found country via iso3166 library: {country} = {iso_country.alpha3}")
                return iso_country.alpha3
        logger.debug(f"iso3166 does not contain {country}")

        #Fallback, can potentially be deleted
        country_code_map = {
            # Country mappings
            # do not implement 'n.a.' here, as this is applied later via language
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
            'Columbia': 'COL',
        }
        
        #language mapping is very important for us!!!
        #https://de.wikipedia.org/wiki/ISO-3166-1-Kodierliste
        language_country_map = {
            'af': 'ZAF',  # Afrikaans -> South Africa
            'ar': 'SAU',  # Arabic -> Saudi Arabia
            'ar-AE': 'ARE',  # Arabic -> United Arab Emirates
            'ar-SA': 'SAU',  # Arabic -> Saudi Arabia
            'bg': 'BGR',  # Bulgarian -> Bulgaria
            'bn': 'BGD',  # Bengali -> Bangladesh
            'cs': 'CZE',  # Czech -> Czech Republic
            'cy': 'GBR',  # Welsh -> United Kingdom
            'da': 'DNK',  # Danish -> Denmark
            'de': 'DEU',  # German -> Germany
            'de-AT': 'AUT',  # Austrian German
            'de-CH': 'CHE',  # Swiss German
            'de-DE': 'DEU',  # German -> Germany
            'el': 'GRC',  # Greek -> Greece
            'en': 'USA',  # English -> United States
            'en-AU': 'AUS',  # Australian English
            'en-CA': 'CAN',  # Canadian English
            'en-GB': 'GBR',  # British English
            'en-IN': 'IND',  # Indian English
            'en-US': 'USA',  # American English
            'es': 'ESP',  # Spanish -> Spain
            'es-AR': 'ARG',  # Argentine Spanish
            'es-CL': 'CHL',  # Chilean Spanish
            'es-CO': 'COL',  # Colombian Spanish
            'es-ES': 'ESP',  # Spanish -> Spain
            'es-MX': 'MEX',  # Mexican Spanish
            'et': 'EST',  # Estonian -> Estonia
            'fa': 'IRN',  # Persian -> Iran
            'fi': 'FIN',  # Finnish -> Finland
            'fr': 'FRA',  # French -> France
            'fr-BE': 'BEL',  # Belgian French
            'fr-CA': 'CAN',  # Canadian French
            'fr-FR': 'FRA',  # French -> France
            'he': 'ISR',  # Hebrew -> Israel
            'hi': 'IND',  # Hindi -> India
            'hr': 'HRV',  # Croatian -> Croatia
            'hu': 'HUN',  # Hungarian -> Hungary
            'id': 'IDN',  # Indonesian -> Indonesia
            'is': 'ISL',  # Icelandic -> Iceland
            'it': 'ITA',  # Italian -> Italy
            'ja': 'JPN',  # Japanese -> Japan
            'ja-JP': 'JPN',  # Japanese -> Japan
            'ka': 'GEO',  # Georgian -> Georgia
            'kk': 'KAZ',  # Kazakh -> Kazakhstan
            'ko': 'KOR',  # Korean -> South Korea
            'lt': 'LTU',  # Lithuanian -> Lithuania
            'lv': 'LVA',  # Latvian -> Latvia
            'mk': 'MKD',  # Macedonian -> North Macedonia
            'ms': 'MYS',  # Malay -> Malaysia
            'nb': 'NOR',  # Norwegian Bokmål -> Norway
            'nl': 'NLD',  # Dutch -> Netherlands
            'nn': 'NOR',  # Norwegian Nynorsk -> Norway
            'no': 'NOR',  # Norwegian -> Norway
            'n.a.': 'ATA',  # not available -> Antarctica
            'pl': 'POL',  # Polish -> Poland
            'pl-PL': 'POL',  # Polish -> Poland
            'pt': 'BRA',  # Portuguese -> Brazil
            'pt-BR': 'BRA',  # Brazilian Portuguese
            'pt-PT': 'PRT',  # European Portuguese
            'ro': 'ROU',  # Romanian -> Romania
            'ru': 'RUS',  # Russian -> Russia
            'sk': 'SVK',  # Slovak -> Slovakia
            'sl': 'SVN',  # Slovenian -> Slovenia
            'sq': 'ALB',  # Albanian -> Albania
            'sr': 'SRB',  # Serbian -> Serbia
            'sv': 'SWE',  # Swedish -> Sweden
            'th': 'THA',  # Thai -> Thailand
            'tr': 'TUR',  # Turkish -> Turkey
            'uk': 'UKR',  # Ukrainian -> Ukraine
            'vi': 'VNM',  # Vietnamese -> Vietnam
            'zh': 'CHN',  # Chinese -> China
            'zh-CN': 'CHN',  # Simplified Chinese -> China
            'zh-HK': 'HKG',  # Traditional Chinese -> Hong Kong
            'zh-TW': 'TWN',  # Traditional Chinese -> Taiwan
        }
        
        code = None
        if country:
            # Try to get from country map first
            code = country_code_map.get(country)
            if code:
                return code
            else:
                if country != "n.a.":
                    logger.warning(f"Did not found a country-code for {country}")
            
        # If language is provided and no country match, try language map
        if language:
            code = language_country_map.get(language)
            if code:
                return code
            else:
                # fallback, use the first two chars of teh language
                code = language_country_map.get(language[:2])
                if code:
                    return code
                else:
                    logger.warning(f"Did not found a country for language {language} or {language[:2]}")
            
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
