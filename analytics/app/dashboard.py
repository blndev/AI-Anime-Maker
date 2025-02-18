import dash
from dash import html, dcc, Input, Output
from flask import send_from_directory
import pandas as pd
import os
import sys
import logging
import sqlite3

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Import data and diagram modules
from .data import get_session_data, get_top_images
from .diagrams_usage import (
    create_sessions_timeline, create_os_chart, create_browser_chart,
    create_mobile_pie, create_generation_status_chart
)
from .diagrams_origin import (
    create_language_chart, create_continent_chart,
    create_country_chart, create_city_chart
)
from .diagrams_uploads import (
    create_image_uploads_timeline,
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

# Initialize the Dash app
app = dash.Dash(__name__, title="AI Anime Maker Analytics")

# Initialize global state for geographic filters
selected_continent = None
selected_country = None

# Get cache directory path from config
config.read_configuration()
CACHE_DIR = os.path.abspath(config.get_output_folder())

# Add route for serving images from cache directory
@app.server.route('/cache/<path:path>')
def serve_image(path):
    """Serve images from cache directory."""
    return send_from_directory(CACHE_DIR, path)

# Initialize with last 30 days of data
initial_end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
initial_start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')

# Get initial data
df = get_session_data(
    initial_start_date, 
    initial_end_date, 
    include_generation_status=True, 
    include_input_data=True
)
top_images_df = get_top_images(df)

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
                    html.Div([
                        html.H2("Geographic Distribution", style=HEADER_STYLE),
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
                                'marginLeft': '20px'
                            }
                        )
                    ], style={'display': 'flex', 'alignItems': 'center'}),
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
                    # Image grid (updated via callback)
                    html.Div(id='image-grid')
                ])
            ]
        )
    ], style={'margin': '20px 0'})
])

# Callback to update image grid
@app.callback(
    Output('image-grid', 'children'),
    [
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_image_grid(start_date, end_date):
    """Update image grid based on selected date range."""
    df = get_session_data(
        start_date,
        end_date,
        include_generation_status=True,
        include_input_data=True
    )
    top_images_df = get_top_images(df)
    
    return html.Div([
        html.Div([
            html.Div([
                html.Img(
                                    src=f'/cache/{os.path.basename(os.path.dirname(path))}/{os.path.basename(path)}' if os.path.exists(path) else '',
                    style={
                        'width': '150px',
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

# Add reset button callback
@app.callback(
    [
        Output('continent-chart', 'clickData', allow_duplicate=True),
        Output('country-chart', 'clickData', allow_duplicate=True)
    ],
    Input('reset-geo-filters', 'n_clicks'),
    prevent_initial_call=True
)
def reset_filters(n_clicks):
    """Reset geographic filters when reset button is clicked."""
    global selected_continent, selected_country
    selected_continent = None
    selected_country = None
    return None, None

# Callback to handle geographic filtering
@app.callback(
    [
        Output('continent-chart', 'figure'),
        Output('country-chart', 'figure'),
        Output('city-chart', 'figure')
    ],
    [
        Input('continent-chart', 'clickData'),
        Input('country-chart', 'clickData'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_geographic_charts(continent_click, country_click, start_date, end_date):
    """Update geographic charts based on click events and date range."""
    global selected_continent, selected_country
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Get current data
    df = get_session_data(
        start_date,
        end_date,
        include_generation_status=True,
        include_input_data=True
    )
    
    # Handle continent click
    if trigger_id == 'continent-chart':
        if continent_click and len(continent_click['points']) > 0:
            new_continent = continent_click['points'][0]['x']
            # Toggle selection if clicking the same continent
            if new_continent == selected_continent:
                selected_continent = None
                selected_country = None  # Reset country when deselecting continent
            else:
                selected_continent = new_continent
                selected_country = None  # Reset country when changing continent
        else:
            selected_continent = None
            selected_country = None
    
    # Handle country click
    elif trigger_id == 'country-chart':
        if country_click and len(country_click['points']) > 0:
            new_country = country_click['points'][0]['x']
            # Toggle selection if clicking the same country
            if new_country == selected_country:
                selected_country = None
            else:
                selected_country = new_country
        else:
            selected_country = None
    
    # Create updated figures
    continent_fig = create_continent_chart(df, selected_continent)
    country_fig = create_country_chart(df, selected_continent, selected_country)
    city_fig = create_city_chart(df, selected_continent, selected_country)
    
    return continent_fig, country_fig, city_fig

# Callback to update all other charts
@app.callback(
    [
        Output('timeline-chart', 'figure'),
        Output('os-chart', 'figure'),
        Output('browser-chart', 'figure'),
        Output('mobile-chart', 'figure'),
        Output('language-chart', 'figure'),
        Output('generation-status-chart', 'figure'),
        Output('image-uploads-timeline', 'figure'),
        Output('top-images-chart', 'figure')
    ],
    [
        Input('continent-chart', 'clickData'),
        Input('country-chart', 'clickData'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_other_charts(continent_click, country_click, start_date, end_date):
    """Update all other charts based on geographic filters and date range."""
    df = get_session_data(
        start_date,
        end_date,
        include_generation_status=True,
        include_input_data=True
    )
    
    # Apply geographic filters consistently
    filtered_df = df.copy()
    if selected_continent:
        filtered_df = filtered_df[filtered_df['Continent'] == selected_continent]
    if selected_country:
        filtered_df = filtered_df[filtered_df['Country'] == selected_country]
    
    # Get filtered top images from the filtered DataFrame
    filtered_top_images_df = get_top_images(filtered_df)
    
    return [
        create_sessions_timeline(filtered_df),
        create_os_chart(filtered_df),
        create_browser_chart(filtered_df),
        create_mobile_pie(filtered_df),
        create_language_chart(filtered_df),
        create_generation_status_chart(filtered_df),
        create_image_uploads_timeline(filtered_df),
        create_top_images_chart(filtered_top_images_df)
    ]

# Get server for external use
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
