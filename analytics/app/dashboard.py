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
    HEADER_STYLE, TAB_STYLE, TAB_SELECTED_STYLE
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
        self.usage_stats_tab = UsageStatisticsTab(self.data_manager)
        self.geo_dist_tab = GeographicDistributionTab(self.data_manager)
        self.gen_details_tab = GenerationDetailsTab(self.data_manager)
        self.image_upload_tab = ImageUploadAnalysisTab(self.data_manager, self.cache_dir)
        
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
                ], style={'textAlign': 'center', 'margin': '20px'}),
            ]),
            
            # Active Filters Display
            html.Div([
                html.Div([
                    html.H2("Active Filters", style=HEADER_STYLE),
                    html.Div(id='active-filters', style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'gap': '10px',
                        'marginRight': '20px'
                    }),
                ], style={'display': 'flex', 'alignItems': 'center'}),
                html.Button(
                    'Reset Filters',
                    id='reset-geo-filters',
                    style={
                        'backgroundColor': '#4CAF50',
                        'color': 'white',
                        'padding': '10px 20px',
                        'border': 'none',
                        'borderRadius': '4px',
                        'cursor': 'pointer',
                        'marginLeft': 'auto'
                    }
                )
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'margin': '20px',
                'padding': '10px',
                'backgroundColor': '#2C3E50',
                'borderRadius': '4px'
            }),
            
            # Store for active filters
            dcc.Store(id='active-filters-store'),
            
            # Tabs
            dcc.Tabs([
                # Tab 1: Usage Statistics
                dcc.Tab(
                    label='Usage Statistics',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=self.usage_stats_tab.create_layout(self.initial_df)
                ),
                
                # Tab 2: Language and Geographic Distribution
                dcc.Tab(
                    label='Language & Geographic Distribution',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=self.geo_dist_tab.create_layout(self.initial_df)
                ),
                
                # Tab 3: Generation Details
                dcc.Tab(
                    label='Generation Details',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=self.gen_details_tab.create_layout(
                        self.initial_start_date,
                        self.initial_end_date
                    )
                ),
                
                # Tab 4: Image Upload Analysis
                dcc.Tab(
                    label='Image Upload Analysis',
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                    children=self.image_upload_tab.create_layout(
                        self.initial_df,
                        self.initial_top_images_df
                    )
                )
            ], style={'margin': '20px 0'})
        ])
    
    def register_callbacks(self):
        """Register all callbacks."""
        # Register tab-specific callbacks
        self.usage_stats_tab.register_callbacks(self.app)
        self.geo_dist_tab.register_callbacks(self.app)
        self.gen_details_tab.register_callbacks(self.app)
        self.image_upload_tab.register_callbacks(self.app)
        
        # Register filter callbacks
        self.register_filter_callbacks()
    
    def register_filter_callbacks(self):
        """Register callbacks for filter management."""
        @self.app.callback(
            Output('active-filters-store', 'data'),
            [
                Input('continent-chart', 'clickData'),
                Input('country-chart', 'clickData'),
                Input('os-chart', 'clickData'),
                Input('browser-chart', 'clickData'),
                Input('language-chart', 'clickData'),
                Input('reset-geo-filters', 'n_clicks')
            ],
            prevent_initial_call=True
        )
        def update_filters_store(continent_click, country_click, os_click, browser_click, language_click, reset_clicks):
            """Update the active filters store."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return dash.no_update
            
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            # Initialize filter values
            filters = {
                'continent': None,
                'country': None,
                'os': None,
                'browser': None,
                'language': None
            }
            
            if trigger_id != 'reset-geo-filters':
                # Handle chart clicks
                if trigger_id == 'continent-chart' and continent_click:
                    filters['continent'] = continent_click['points'][0]['x']
                elif trigger_id == 'country-chart' and country_click:
                    filters['country'] = country_click['points'][0]['x']
                elif trigger_id == 'os-chart' and os_click:
                    filters['os'] = os_click['points'][0]['x']
                elif trigger_id == 'browser-chart' and browser_click:
                    filters['browser'] = browser_click['points'][0]['x']
                elif trigger_id == 'language-chart' and language_click:
                    filters['language'] = language_click['points'][0]['x']
            
            return filters
        
        @self.app.callback(
            Output('active-filters', 'children'),
            Input('active-filters-store', 'data')
        )
        def update_active_filters_display(data):
            """Update the active filters display."""
            if not data or not any(data.values()):
                return [
                    html.Div("No filters active", style={
                        'color': '#95A5A6',
                        'fontStyle': 'italic'
                    })
                ]
            
            filters = []
            
            # Geographic filters
            if data.get('continent'):
                filters.append(
                    html.Div([
                        html.Strong("Continent: "),
                        html.Span(data['continent'])
                    ], style={
                        'backgroundColor': '#34495E',
                        'padding': '5px 10px',
                        'borderRadius': '4px',
                        'marginRight': '10px'
                    })
                )
            
            if data.get('country'):
                filters.append(
                    html.Div([
                        html.Strong("Country: "),
                        html.Span(data['country'])
                    ], style={
                        'backgroundColor': '#34495E',
                        'padding': '5px 10px',
                        'borderRadius': '4px',
                        'marginRight': '10px'
                    })
                )
            
            # Platform filters
            if data.get('os'):
                filters.append(
                    html.Div([
                        html.Strong("OS: "),
                        html.Span(data['os'])
                    ], style={
                        'backgroundColor': '#2980B9',
                        'padding': '5px 10px',
                        'borderRadius': '4px',
                        'marginRight': '10px'
                    })
                )
            
            if data.get('browser'):
                filters.append(
                    html.Div([
                        html.Strong("Browser: "),
                        html.Span(data['browser'])
                    ], style={
                        'backgroundColor': '#2980B9',
                        'padding': '5px 10px',
                        'borderRadius': '4px',
                        'marginRight': '10px'
                    })
                )
            
            # Language filter
            if data.get('language'):
                filters.append(
                    html.Div([
                        html.Strong("Language: "),
                        html.Span(data['language'])
                    ], style={
                        'backgroundColor': '#8E44AD',
                        'padding': '5px 10px',
                        'borderRadius': '4px',
                        'marginRight': '10px'
                    })
                )
            
            return filters

# Create dashboard instance for external use
dashboard = Dashboard()
app = dashboard.app
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
