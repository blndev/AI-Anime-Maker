import dash
from dash import html, dcc, Input, Output
from flask import send_from_directory
import pandas as pd
import os
import sys
import logging
import sqlite3
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Import data and diagram modules
from .data import get_session_data, get_top_uploaded_images, get_top_generated_images
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
    create_top_uploaded_images_chart,
    create_top_generated_images_chart
)
from .diagrams_generations import create_style_usage_chart

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

# Initialize global state for filters
selected_continent = None
selected_country = None
selected_os = None
selected_browser = None
selected_language = None

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

# Get local timezone
local_tz = datetime.now().astimezone().tzinfo

# Get initial data
df = get_session_data(
    initial_start_date, 
    initial_end_date, 
    include_generation_status=True, 
    include_input_data=True,
    timezone=local_tz
)
top_images_df = get_top_uploaded_images(df)

# Create layout
app.layout = html.Div(style=LAYOUT_STYLE, children=[
    html.H1(f"{config.get_app_title()} Analytics Dashboard", style=HEADER_STYLE),
    
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
        
        # Tab 3: Generation Details
        dcc.Tab(
            label='Generation Details',
            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE,
            children=[
                # Style Usage Section
                html.Div([
                    html.H2("Generation Style Usage", style=HEADER_STYLE),
                    dcc.Graph(id='style-usage-chart', figure=create_style_usage_chart(df))
                ])
            ]
        ),
        
        # Tab 4: Image Upload Analysis
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
                    dcc.Graph(id='top-images-chart', figure=create_top_uploaded_images_chart(top_images_df)),
                    # Image grid (updated via callback)
                    html.Div(id='image-grid')
                ]),
                
                # Top Generated Images Section with Details
                html.Div([
                    html.H2("Most Used for Generations", style=HEADER_STYLE),
                    html.Div([
                        # Left column: Chart
                        html.Div([
                            dcc.Graph(id='top-generated-images-chart', figure=create_top_generated_images_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        
                        # Right column: Details
                        html.Div([
                            html.H3("Image Details", style=HEADER_STYLE),
                            html.Div(id='generation-image-details', children=[
                                html.Div("Select an image to view details", style={
                                    'color': '#95A5A6',
                                    'fontStyle': 'italic',
                                    'textAlign': 'center',
                                    'marginTop': '20px'
                                })
                            ])
                        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'})
                    ])
                ])
            ]
        )
    ], style={'margin': '20px 0'})
])

# Callback to update image grid
@app.callback(
    Output('image-grid', 'children'),
    [
        Input('active-filters-store', 'data'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_image_grid(filters_data, start_date, end_date):
    """Update image grid based on filters and date range."""
    df = get_session_data(
        start_date,
        end_date,
        include_generation_status=True,
        include_input_data=True,
        timezone=local_tz
    )
    
    # Apply all filters
    filtered_df = df.copy()
    if filters_data:
        # Geographic filters
        if filters_data.get('continent'):
            filtered_df = filtered_df[filtered_df['Continent'] == filters_data['continent']]
        if filters_data.get('country'):
            filtered_df = filtered_df[filtered_df['Country'] == filters_data['country']]
        
        # Platform filters
        if filters_data.get('os'):
            filtered_df = filtered_df[filtered_df['OS'] == filters_data['os']]
        if filters_data.get('browser'):
            filtered_df = filtered_df[filtered_df['Browser'] == filters_data['browser']]
        
        # Language filter
        if filters_data.get('language'):
            filtered_df = filtered_df[filtered_df['Language'] == filters_data['language']]
    
    top_images_df = get_top_uploaded_images(filtered_df)
    
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

# Callback to update active filters store
@app.callback(
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
    
    global selected_continent, selected_country, selected_os, selected_browser, selected_language
    
    if trigger_id == 'reset-geo-filters':
        selected_continent = None
        selected_country = None
        selected_os = None
        selected_browser = None
        selected_language = None
    elif trigger_id == 'continent-chart':
        if continent_click and len(continent_click['points']) > 0:
            new_continent = continent_click['points'][0]['x']
            if new_continent == selected_continent:
                selected_continent = None
                selected_country = None
            else:
                selected_continent = new_continent
                selected_country = None
        else:
            selected_continent = None
            selected_country = None
    elif trigger_id == 'country-chart':
        if country_click and len(country_click['points']) > 0:
            new_country = country_click['points'][0]['x']
            if new_country == selected_country:
                selected_country = None
            else:
                selected_country = new_country
        else:
            selected_country = None
    elif trigger_id == 'os-chart':
        if os_click and len(os_click['points']) > 0:
            new_os = os_click['points'][0]['x']
            if new_os == selected_os:
                selected_os = None
            else:
                selected_os = new_os
        else:
            selected_os = None
    elif trigger_id == 'browser-chart':
        if browser_click and len(browser_click['points']) > 0:
            new_browser = browser_click['points'][0]['x']
            if new_browser == selected_browser:
                selected_browser = None
            else:
                selected_browser = new_browser
        else:
            selected_browser = None
    elif trigger_id == 'language-chart':
        if language_click and len(language_click['points']) > 0:
            new_language = language_click['points'][0]['x']
            if new_language == selected_language:
                selected_language = None
            else:
                selected_language = new_language
        else:
            selected_language = None
    
    return {
        'continent': selected_continent,
        'country': selected_country,
        'os': selected_os,
        'browser': selected_browser,
        'language': selected_language
    }

# Callback to update active filters display
@app.callback(
    Output('active-filters', 'children'),
    Input('active-filters-store', 'data')
)
def update_active_filters_display(data):
    """Update the active filters display."""
    if not data:
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
    
    if not filters:
        filters.append(
            html.Div("No filters active", style={
                'color': '#95A5A6',
                'fontStyle': 'italic'
            })
        )
    
    return filters

# Callback to handle geographic filtering
@app.callback(
    [
        Output('continent-chart', 'figure'),
        Output('country-chart', 'figure'),
        Output('city-chart', 'figure')
    ],
    [
        Input('active-filters-store', 'data'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_geographic_charts(filters_data, start_date, end_date):
    """Update geographic charts based on active filters and date range."""
    if not filters_data:
        return dash.no_update
    
    # Get current data
    df = get_session_data(
        start_date,
        end_date,
        include_generation_status=True,
        include_input_data=True,
        timezone=local_tz
    )
    
    # Apply non-geographic filters first
    filtered_df = df.copy()
    if filters_data:
        # Platform filters
        if filters_data.get('os'):
            filtered_df = filtered_df[filtered_df['OS'] == filters_data['os']]
        if filters_data.get('browser'):
            filtered_df = filtered_df[filtered_df['Browser'] == filters_data['browser']]
        
        # Language filter
        if filters_data.get('language'):
            filtered_df = filtered_df[filtered_df['Language'] == filters_data['language']]
    
    # Create updated figures with filtered data
    continent_fig = create_continent_chart(filtered_df, filters_data.get('continent'))
    country_fig = create_country_chart(filtered_df, filters_data.get('continent'), filters_data.get('country'))
    city_fig = create_city_chart(filtered_df, filters_data.get('continent'), filters_data.get('country'))
    
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
        Output('top-images-chart', 'figure'),
        Output('top-generated-images-chart', 'figure'),
        Output('style-usage-chart', 'figure')
    ],
    [
        Input('active-filters-store', 'data'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_other_charts(filters_data, start_date, end_date):
    """Update all other charts based on active filters and date range."""
    df = get_session_data(
        start_date,
        end_date,
        include_generation_status=True,
        include_input_data=True,
        timezone=local_tz
    )
    
    # Apply all filters
    filtered_df = df.copy()
    if filters_data:
        # Geographic filters
        if filters_data.get('continent'):
            filtered_df = filtered_df[filtered_df['Continent'] == filters_data['continent']]
        if filters_data.get('country'):
            filtered_df = filtered_df[filtered_df['Country'] == filters_data['country']]
        
        # Platform filters
        if filters_data.get('os'):
            filtered_df = filtered_df[filtered_df['OS'] == filters_data['os']]
        if filters_data.get('browser'):
            filtered_df = filtered_df[filtered_df['Browser'] == filters_data['browser']]
        
        # Language filter
        if filters_data.get('language'):
            filtered_df = filtered_df[filtered_df['Language'] == filters_data['language']]
    
    # Get filtered top images
    filtered_top_images_df = get_top_uploaded_images(filtered_df)
    
    return [
        create_sessions_timeline(filtered_df),
        create_os_chart(filtered_df),
        create_browser_chart(filtered_df),
        create_mobile_pie(filtered_df),
        create_language_chart(filtered_df),
        create_generation_status_chart(filtered_df),
        create_image_uploads_timeline(filtered_df),
        create_top_uploaded_images_chart(filtered_top_images_df),
        create_top_generated_images_chart(filtered_df),
        create_style_usage_chart(filtered_df)
    ]

# Callback to update image details for both charts
@app.callback(
    Output('generation-image-details', 'children'),
    [
        Input('top-generated-images-chart', 'clickData'),
        Input('top-images-chart', 'clickData')
    ]
)
def update_image_details(generation_click, upload_click):
    """Update the details display when a bar in either chart is clicked."""
    # Use the most recent click data
    ctx = dash.callback_context
    if not ctx.triggered:
        return html.Div("Select an image to view details", style={
            'color': '#95A5A6',
            'fontStyle': 'italic',
            'textAlign': 'center',
            'marginTop': '20px'
        })
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    click_data = generation_click if trigger_id == 'top-generated-images-chart' else upload_click
    if not click_data or not click_data.get('points'):
        return html.Div("Select an image to view details", style={
            'color': '#95A5A6',
            'fontStyle': 'italic',
            'textAlign': 'center',
            'marginTop': '20px'
        })
    
    if not click_data or not click_data.get('points'):
        return html.Div("Select an image to view details", style={
            'color': '#95A5A6',
            'fontStyle': 'italic',
            'textAlign': 'center',
            'marginTop': '20px'
        })
    
    # Get the selected image details from the click data
    selected_id = click_data['points'][0]['x']
    selected_path = click_data['points'][0]['customdata'][0]
    selected_token = click_data['points'][0]['customdata'][1]
    selected_face = click_data['points'][0]['customdata'][2]
    selected_gender = click_data['points'][0]['customdata'][3]
    
    logger.debug(f"Selected ID/SHA1: {selected_id}")
    logger.debug(f"Selected path: {selected_path}")
    
    # Get the image details from the database
    df = get_session_data(
        initial_start_date,
        initial_end_date,
        include_generation_status=True,
        include_input_data=True,
        timezone=local_tz
    )
    
    # Get details based on which chart was clicked
    if trigger_id == 'top-generated-images-chart':
        # Extract SHA1 from "SHA1: {sha1}..." format
        raw_sha1 = selected_id.split(': ')[1].split('...')[0]
        logger.debug(f"Extracted SHA1: {raw_sha1}")
        df_details = get_top_generated_images(df)
        filtered_details = df_details[df_details['SHA1'].str.contains(raw_sha1, regex=False)]
    else:
        # Extract ID from "ID: {id}" format
        raw_id = selected_id.split(': ')[1]
        logger.debug(f"Extracted ID: {raw_id}")
        df_details = get_top_uploaded_images(df)
        filtered_details = df_details[df_details['ID'].astype(str) == raw_id]
    
    logger.debug(f"Found {len(filtered_details)} matching images")
    
    if len(filtered_details) == 0:
        return html.Div("Image details not found", style={
            'color': '#95A5A6',
            'fontStyle': 'italic',
            'textAlign': 'center',
            'marginTop': '20px'
        })
    
    image_data = filtered_details.iloc[0]
    
    # Convert upload time to local timezone if available
    upload_time = pd.to_datetime(image_data['UploadTime']).tz_localize('GMT').tz_convert(local_tz) if 'UploadTime' in image_data else None
    
    # Create details display with count label based on chart type
    count_label = "Generations" if trigger_id == 'top-generated-images-chart' else "Uploads"
    count_value = image_data['GenerationCount'] if trigger_id == 'top-generated-images-chart' else image_data['UploadCount']
    
    details = [
        html.Div([
            html.Img(
                src=f'/cache/{os.path.basename(os.path.dirname(selected_path))}/{os.path.basename(selected_path)}',
                style={
                    'width': '200px',
                    'objectFit': 'cover',
                    'margin': '10px auto',
                    'display': 'block',
                    'border': '2px solid #333'
                }
            ),
            html.Div([
                html.Strong("Input ID: "),
                html.Span(str(image_data['ID']) if pd.notna(image_data['ID']) else 'N/A')
            ], style={'margin': '5px 0'}),
            html.Div([
                html.Strong("SHA1: "),
                html.Span(image_data['SHA1'] if pd.notna(image_data['SHA1']) else 'N/A')
            ], style={'margin': '5px 0'}),
            html.Div([
                html.Strong("Token: "),
                html.Span(image_data['Token'] if pd.notna(image_data['Token']) else 'N/A')
            ], style={'margin': '5px 0'}),
            html.Div([
                html.Strong("Face: "),
                html.Span("Yes" if image_data['Face'] else "No")
            ], style={'margin': '5px 0'}),
            html.Div([
                html.Strong("Gender: "),
                html.Span(image_data['Gender'] if pd.notna(image_data['Gender']) else 'N/A')
            ], style={'margin': '5px 0'}),
            html.Div([
                html.Strong("Age Range: "),
                html.Span(f"{image_data['MinAge'] if pd.notna(image_data['MinAge']) else 'N/A'} - {image_data['MaxAge'] if pd.notna(image_data['MaxAge']) else 'N/A'}")
            ], style={'margin': '5px 0'}),
            *([html.Div([
                html.Strong("Upload Time: "),
                html.Span(upload_time.strftime('%Y-%m-%d %H:%M:%S %Z'))
            ], style={'margin': '5px 0'})] if upload_time is not None else []),
            html.Div([
                html.Strong(f"{count_label}: "),
                html.Span(str(count_value))
            ], style={'margin': '5px 0'})
        ], style={
            'backgroundColor': '#2C3E50',
            'padding': '15px',
            'borderRadius': '8px',
            'margin': '10px'
        })
    ]
    
    return details

# Get server for external use
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
