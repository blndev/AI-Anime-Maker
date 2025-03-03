import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analytics.app.data_manager import DataManager

#TODO: create a test database in memory or in filesystem first
@unittest.skip("create a test database first via init analytics and generate_testdata")
class TestDataManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock config and database connection
        self.config_patcher = patch('analytics.app.data_manager.config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.get_analytics_db_path.return_value = ':memory:'
        
        # Initialize DataManager with mocked dependencies
        self.data_manager = DataManager()
        
    def tearDown(self):
        """Clean up after each test method."""
        self.config_patcher.stop()

    def test_initialization(self):
        """Test DataManager initialization."""
        self.assertIsNotNone(self.data_manager)
        self.assertEqual(self.data_manager._filters['continent'], None)
        self.assertEqual(self.data_manager._filters['country'], None)
        self.assertEqual(self.data_manager._filters['os'], None)
        self.assertEqual(self.data_manager._filters['browser'], None)
        self.assertEqual(self.data_manager._filters['language'], None)

    def test_filter_management(self):
        """Test filter management functions."""
        # Test adding filters
        self.data_manager.add_filter('continent', 'Europe')
        self.assertEqual(self.data_manager._filters['continent'], 'Europe')
        
        self.data_manager.add_filter('country', 'Germany')
        self.assertEqual(self.data_manager._filters['country'], 'Germany')
        
        # Test invalid filter type
        with self.assertRaises(ValueError):
            self.data_manager.add_filter('invalid_filter', 'value')
        
        # Test removing filters
        self.data_manager.remove_filter('continent')
        self.assertIsNone(self.data_manager._filters['continent'])
        
        # Test resetting filters
        self.data_manager.reset_filters()
        self.assertIsNone(self.data_manager._filters['country'])
        
        # Test getting active filters
        self.data_manager.add_filter('os', 'Windows')
        active_filters = self.data_manager.get_active_filters()
        self.assertEqual(len(active_filters), 1)
        self.assertEqual(active_filters['os'], 'Windows')

    def test_country_code_conversion(self):
        """Test country code conversion functionality."""
        # Test direct country matches
        self.assertEqual(self.data_manager.get_country_code_from_country('Germany'), 'DEU')
        self.assertEqual(self.data_manager.get_country_code_from_country('United States'), 'USA')
        
        # Test language-based fallbacks
        self.assertEqual(self.data_manager.get_country_code_from_country(None, 'en'), 'USA')
        self.assertEqual(self.data_manager.get_country_code_from_country(None, 'de'), 'DEU')
        self.assertEqual(self.data_manager.get_country_code_from_country(None, 'fr'), 'FRA')
        
        # Test language variants
        self.assertEqual(self.data_manager.get_country_code_from_country(None, 'en-US'), 'USA')
        self.assertEqual(self.data_manager.get_country_code_from_country(None, 'en-GB'), 'GBR')
        self.assertEqual(self.data_manager.get_country_code_from_country(None, 'de-AT'), 'AUT')
        
        # Test unknown values
        self.assertEqual(self.data_manager.get_country_code_from_country('Unknown'), 'UNK')
        self.assertEqual(self.data_manager.get_country_code_from_country(None, 'unknown-lang'), None)

    def test_city_coordinates(self):
        """Test city coordinates functionality."""
        # Create mock city data
        mock_city_data = pd.DataFrame({
            'City': ['Berlin', 'Paris', 'London'],
            'Country': ['Germany', 'France', 'United Kingdom'],
            'State': [None, None, None],
            'Longitude': [13.4050, 2.3522, -0.1276],
            'Latitude': [52.5200, 48.8566, 51.5074]
        })
        
        # Mock the csv reading
        with patch('pandas.read_csv', return_value=mock_city_data):
            self.data_manager._city_coords = self.data_manager._load_city_coordinates()
        
        # Test getting coordinates
        berlin_coords = self.data_manager.get_city_coordinates('Berlin', 'Germany')
        self.assertIsNotNone(berlin_coords)
        self.assertEqual(berlin_coords[0], 13.4050)  # longitude
        self.assertEqual(berlin_coords[1], 52.5200)  # latitude
        
        # Test unknown city
        unknown_coords = self.data_manager.get_city_coordinates('Unknown City', 'Unknown Country')
        self.assertIsNone(unknown_coords)
        
        # Test None/Unknown values
        self.assertIsNone(self.data_manager.get_city_coordinates(None, 'Germany'))
        self.assertIsNone(self.data_manager.get_city_coordinates('Unknown', 'Germany'))

    @patch('sqlite3.connect')
    def test_data_preparation(self, mock_connect):
        """Test data preparation and filtering."""
        # Create mock data
        # Create timestamps as they would come from SQLite (naive datetime strings)
        timestamps = [
            '2024-01-01 10:00:00',
            '2024-01-01 11:00:00',
            '2024-01-02 10:00:00',
            '2024-01-02 11:00:00'
        ]
        
        mock_data = pd.DataFrame({
            'Session': ['1', '2', '3', '4'],
            'Country': ['Germany', 'France', 'Germany', 'Spain'],
            'Continent': ['Europe', 'Europe', 'Europe', 'Europe'],
            'OS': ['Windows', 'Mac', 'Windows', 'Linux'],
            'Browser': ['Chrome', 'Safari', 'Firefox', 'Chrome'],
            'Language': ['de', 'fr', 'de', 'es'],
            'CountryCode': ['DEU', 'FRA', 'DEU', 'ESP'],
            'Timestamp': timestamps,
            'Date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02'],
            'ImageUploads': [1, 0, 2, 1],
            'GenerationCount': [2, 0, 3, 1],
            'HasStartedGeneration': [1, 0, 1, 1],
            'CachePaths': ['path1', None, 'path2,path3', 'path4']
        })
        
        # Mock the database query
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_cursor
        with patch('pandas.read_sql_query', return_value=mock_data):
            # Test without filters
            df = self.data_manager.prepare_filtered_data('2024-01-01', '2024-01-31')
            self.assertEqual(len(df), 4)
            
            # Test with country filter
            self.data_manager.add_filter('country', 'Germany')
            df = self.data_manager.prepare_filtered_data('2024-01-01', '2024-01-31')
            self.assertEqual(len(df), 2)
            self.assertTrue(all(df['Country'] == 'Germany'))
            
            # Test with multiple filters
            self.data_manager.add_filter('os', 'Windows')
            df = self.data_manager.prepare_filtered_data('2024-01-01', '2024-01-31')
            self.assertEqual(len(df), 2)
            self.assertTrue(all(df['Country'] == 'Germany'))
            self.assertTrue(all(df['OS'] == 'Windows'))

if __name__ == '__main__':
    unittest.main()
