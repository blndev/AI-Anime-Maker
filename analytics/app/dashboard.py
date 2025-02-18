import dash
from dash import html, dcc, Input, Output
from flask import send_from_directory
import pandas as pd
import sqlite3
import os
import sys
import logging

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Import diagram modules
from .diagrams_usage import (
    create_sessions_timeline, create_os_chart, create_browser_chart,
    create_mobile_pie, create_generation_status_chart
)
from .diagrams_origin import (
    create_language_chart, create_continent_chart,
    create_country_chart, create_city_chart
)
from .diagrams_uploads import (
    get_top_images, create_image_uploads_timeline,
    create_top_images_chart
)

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

def get_session_data(start_date=None, end_date=None, include_generation_status=False, include_input_data=False):
    """Get session data from analytics database.
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
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
    logger.info(f"Data loaded: {len(df)} rows")
    if len(df) > 0:
        logger.debug(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        logger.debug(f"Sample dates: {df['Date'].head().tolist()}")
    
    return df

# Initialize the Dash app
app = dash.Dash(__name__, title="AI Anime Maker Analytics")

# Get cache directory path from config
config.read_configuration()
CACHE_DIR = os.path.abspath(config.get_cache_folder())

# Add route for serving images from cache directory
@app.server.route('/cache/<path:path>')
def serve_image(path):
    """Serve images from cache directory."""
    return send_from_directory(CACHE_DIR, path)

# Initialize with last 30 days of data
initial_end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
initial_start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')

# Get initial data
df = get_session_data(initial_start_date, initial_end_date, include_generation_status=True, include_input_data=True)
top_images_df = get_top_images()

# Create layout
app.layout = html.Div(style=LAYOUT_STYLE, children=[
    html.H1("AI Anime Maker Analytics Dashboard", style=HEADER_STYLE),
    
    # Date Range Selector
    html.Div([
        html.H2("Date Range Selection", style=HEADER_STYLE),
        html.Div([
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed='2024-01-01',  # Adjust as needed
                max_date_allowed=initial_end_date,
                start_date=initial_start_date,
                end_date=initial_end_date,
                display_format='YYYY-MM-DD'
            )
        ], style={'textAlign': 'center', 'margin': '20px'}),
    ]),
    
    # Tabs
    dcc.Tabs([
        # Tab 1: Usage Statistics
        dcc.Tab(
            label='Usage Statistics',
            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE,
            children=[
                # Sessions Timeline
                html.Div([
                    dcc.Graph(id='timeline-chart', figure=create_sessions_timeline(df))
                ]),
                
                # Platform Statistics Section
                html.Div([
                    html.H2("Platform Statistics", style=HEADER_STYLE),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='os-chart', figure=create_os_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            dcc.Graph(id='browser-chart', figure=create_browser_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='mobile-chart', figure=create_mobile_pie(df))
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            dcc.Graph(id='generation-status-chart', figure=create_generation_status_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ])
                ])
            ]
        ),
        
        # Tab 2: Language and Geographic Distribution
        dcc.Tab(
            label='Language & Geographic Distribution',
            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE,
            children=[
                # Language Distribution Section
                html.Div([
                    html.H2("Language Distribution", style=HEADER_STYLE),
                    dcc.Graph(id='language-chart', figure=create_language_chart(df))
                ]),
                
                # Geographic Distribution Section
                html.Div([
                    html.H2("Geographic Distribution", style=HEADER_STYLE),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='continent-chart', figure=create_continent_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            dcc.Graph(id='country-chart', figure=create_country_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    html.Div([
                        dcc.Graph(id='city-chart', figure=create_city_chart(df))
                    ])
                ])
            ]
        ),
        
        # Tab 3: Image Upload Analysis
        dcc.Tab(
            label='Image Upload Analysis',
            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE,
            children=[
                # Image Uploads Timeline
                html.Div([
                    html.H2("Image Upload Patterns", style=HEADER_STYLE),
                    dcc.Graph(id='image-uploads-timeline', figure=create_image_uploads_timeline(df))
                ]),
                
                # Top Images Section
                html.Div([
                    html.H2("Most Uploaded Images", style=HEADER_STYLE),
                    # Bar chart showing upload counts
                    dcc.Graph(id='top-images-chart', figure=create_top_images_chart(top_images_df)),
                    # Image grid
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Img(
                                    src=f'/cache/{os.path.relpath(path, config.get_cache_folder())}' if os.path.exists(path) else '',
                                    style={
                                        'width': '150px',
                                        #'height': '150px',
                                        'object-fit': 'cover',
                                        'margin': '5px',
                                        'border': '2px solid #333'
                                    }
                                ),
                                html.Div(
                                    f'Uploaded {count} times',
                                    style={
                                        'color': '#FFFFFF',
                                        'textAlign': 'center',
                                        'marginTop': '5px'
                                    }
                                )
                            ], style={
                                'display': 'flex',
                                'flexDirection': 'column',
                                'alignItems': 'center',
                                'margin': '10px'
                            }) for path, count in zip(top_images_df['CachePath'], top_images_df['UploadCount'])
                        ], style={
                            'display': 'flex',
                            'flexWrap': 'wrap',
                            'justifyContent': 'center',
                            'gap': '20px',
                            'margin': '20px 0'
                        })
                    ])
                ])
            ]
        )
    ], style={'margin': '20px 0'})
])

# Callback to update all charts when date range changes
@app.callback(
    [
        Output('timeline-chart', 'figure'),
        Output('os-chart', 'figure'),
        Output('browser-chart', 'figure'),
        Output('mobile-chart', 'figure'),
        Output('continent-chart', 'figure'),
        Output('country-chart', 'figure'),
        Output('city-chart', 'figure'),
        Output('language-chart', 'figure'),
        Output('generation-status-chart', 'figure'),
        Output('image-uploads-timeline', 'figure'),
        Output('top-images-chart', 'figure')
    ],
    [
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_charts(start_date, end_date):
    """Update all charts based on selected date range."""
    df = get_session_data(start_date, end_date, include_generation_status=True, include_input_data=True)
    top_images_df = get_top_images()
    return [
        create_sessions_timeline(df),
        create_os_chart(df),
        create_browser_chart(df),
        create_mobile_pie(df),
        create_continent_chart(df),
        create_country_chart(df),
        create_city_chart(df),
        create_language_chart(df),
        create_generation_status_chart(df),
        create_image_uploads_timeline(df),
        create_top_images_chart(top_images_df)
    ]

# Get server for external use
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
