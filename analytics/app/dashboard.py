import dash
from dash import html, dcc, Input, Output
from flask import send_from_directory
import pandas as pd
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Import data manager and tab modules
from .data_manager import DataManager
from .tabs.usage_statistics import UsageStatisticsTab
from .tabs.geographic_distribution import GeographicDistributionTab
from .tabs.generation_details import GenerationDetailsTab
from .tabs.image_upload_analysis import ImageUploadAnalysisTab

# Import styles
from .styles import (
    PLOTLY_TEMPLATE, LAYOUT_THEME, LAYOUT_STYLE,
    HEADER_STYLE, TAB_STYLE, TAB_SELECTED_STYLE,
    FILTER_CONTAINER_STYLE, FILTER_BUTTON_STYLE, FILTER_DISPLAY_STYLE,
    FILTER_TAG_STYLE, PLATFORM_FILTER_STYLE, LANGUAGE_FILTER_STYLE,
    NO_DATA_STYLE, DATE_PICKER_CONTAINER_STYLE, FILTER_HEADER_STYLE,
    CHART_CONTAINER_STYLE, TABS_CONTAINER_STYLE
)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with formatting
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(console_handler)

class Dashboard:
    def __init__(self):
        """Initialize the Dashboard application."""
        # Initialize the Dash app
        self.app = dash.Dash(__name__, title="AI Anime Maker Analytics")
        
        # Get cache directory path from config
        config.read_configuration()
        self.cache_dir = os.path.abspath(config.get_output_folder())
        
        # Initialize with last 30 days of data
        self.initial_end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
        self.initial_start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Initialize DataManager
        self.data_manager = DataManager()
        
        # Get initial data
        self.initial_df = self.data_manager.prepare_filtered_data(
            self.initial_start_date,
            self.initial_end_date
        )
        self.initial_top_images_df = self.data_manager.get_top_uploaded_images()
        
        # Initialize tabs
        self.usage_stats_tab = UsageStatisticsTab(self.data_manager, self.app)
        self.geo_dist_tab = GeographicDistributionTab(self.data_manager, self.app)
        self.gen_details_tab = GenerationDetailsTab(self.data_manager, self.app)
        self.image_upload_tab = ImageUploadAnalysisTab(self.data_manager, self.cache_dir, self.app)
        
        # Create layout
        self.app.layout = self.create_layout()
        
        # Register callbacks
        self.register_callbacks()
        
        # Add route for serving images from cache directory
        @self.app.server.route('/cache/<path:path>')
        def serve_image(path):
            """Serve images from cache directory."""
            return send_from_directory(self.cache_dir, path)
    
    def create_layout(self):
        """Create the dashboard layout."""
        return html.Div(style=LAYOUT_STYLE, children=[
            html.H1(f"{config.get_app_title()} Analytics Dashboard", style=HEADER_STYLE),
            
            # Date Range Selector
            html.Div([
                html.H2("Date Range Selection", style=HEADER_STYLE),
                html.Div([
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed='2024-01-01',  # Adjust as needed
                        max_date_allowed=self.initial_end_date,
                        start_date=self.initial_start_date,
                        end_date=self.initial_end_date,
                        display_format='YYYY-MM-DD'
                    )
                ], style=DATE_PICKER_CONTAINER_STYLE),
            ]),
            
            # Active Filters Display
            html.Div([
                html.Div([
                    html.H2("Active Filters", style=HEADER_STYLE),
                    html.Div(id='active-filters', style=FILTER_DISPLAY_STYLE),
                ], style=FILTER_HEADER_STYLE),
                html.Button(
                    'Reset Filters',
                    id='reset-geo-filters',
                    style=FILTER_BUTTON_STYLE
                )
            ], style=FILTER_CONTAINER_STYLE),
            
            # Tabs
            dcc.Tabs([
                # Tab 1: Usage Statistics
                dcc.Tab(
                    label='Usage',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=self.usage_stats_tab.create_layout(self.initial_df)
                ),
                
                # Tab 2: Language and Geographic Distribution
                dcc.Tab(
                    label='Geographic',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=self.geo_dist_tab.create_layout(self.initial_df)
                ),
                
                # Tab 3: Image Upload Analysis
                dcc.Tab(
                    label='Image Upload Analysis',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=self.image_upload_tab.create_layout(
                        self.initial_df,
                        self.initial_top_images_df
                    )
                ),

                # Tab 4: Generation Details
                dcc.Tab(
                    label='Generation Details',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=self.gen_details_tab.create_layout(
                        self.initial_start_date,
                        self.initial_end_date
                    )
                )
                
            ], style=TABS_CONTAINER_STYLE)
        ])
    
    def register_callbacks(self):
        """Register all callbacks."""
        # No more callbacks to register

# Create dashboard instance for external use
dashboard = Dashboard()
app = dashboard.app
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
