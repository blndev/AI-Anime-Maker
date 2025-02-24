import os
from dash import html, dcc, Input, Output, State, callback, ctx, ALL
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import logging

# Set up logging
logger = logging.getLogger(__name__)
from ..styles import (
    HEADER_STYLE, PLOTLY_TEMPLATE, LAYOUT_THEME, CONTENT_STYLE,
    SEARCH_CONTAINER_STYLE, SEARCH_INPUT_STYLE, SEARCH_BUTTON_STYLE,
    TABLE_STYLE, TABLE_HEADER_STYLE, TABLE_CELL_STYLE
)

class AdHocQueriesTab:
    def __init__(self, data_manager, app):
        """Initialize the Generation Details tab with a DataManager instance."""
        logger.info("Initializing Generation Details tab")
        self.data_manager = data_manager
        self.app = app
        self.register_callbacks()
        logger.info("Generation Details tab initialized successfully")
        
    def create_layout(self, initial_start_date, initial_end_date):
        """Create the layout for the Generation Details tab."""
        return [
            # Modal for full-size image view
            dcc.Store(id='adhoc_current-image-src', data=None),
            html.Div(
                id='adhoc_image-modal',
                style={
                    'display': 'none',
                    'position': 'fixed',
                    'zIndex': 1000,
                    'left': 0,
                    'top': 0,
                    'width': '100%',
                    'height': '100%',
                    'backgroundColor': 'rgba(0,0,0,0.9)',
                    'cursor': 'pointer'
                },
                children=[
                    html.Img(
                        id='adhoc_modal-image',
                        style={
                            'margin': 'auto',
                            'display': 'block',
                            'maxWidth': '90%',
                            'maxHeight': '90%',
                            'position': 'relative',
                            'top': '50%',
                            'transform': 'translateY(-50%)'
                        }
                    )
                ]
            ),
            # Search Section
            html.Div([
                html.H2("Search by Input ID or SHA1", style=HEADER_STYLE),
                html.Div([
                    dcc.Input(
                        id='adhoc_image_search',
                        type='text',
                        placeholder='Enter Input ID or SHA1',
                        style={**SEARCH_INPUT_STYLE, 'width': '300px'}
                    ),
                    html.Button('Search', id='adhoc_search-button', n_clicks=0, style=SEARCH_BUTTON_STYLE)
                ], style=SEARCH_CONTAINER_STYLE),
                
                # Results Section
                html.Div(id='adhoc_search-results', style={'marginBottom': '30px'}),
                
                html.Div(id='adhoctable', style={'marginBottom': '30px'})
            ], style=CONTENT_STYLE)
        ]

    def create_image_details(self, image_data):
        """Create a details panel for the input image."""
        return html.Div([
            html.H3("Image Details"),
            html.Div([
                html.Img(
                    src= os.path.join("/cache", image_data['CachePath']),
                    style={'maxWidth': '200px', 'marginRight': '20px', 'cursor': 'pointer'},
                    id={'type': 'preview-image', 'index': 'input-image'},
                    title='Click to enlarge'
                ),
                html.Div([
                    html.P(f"Input ID: {image_data['ID']}"),
                    html.P(f"SHA1: {image_data['SHA1']}"),
                    html.P(f"Session: {image_data['Session']}"),
                    html.P(f"Token received: {image_data['Token']}"),
                    html.P(f"Face Detected: {image_data['Face']}"),
                    html.P(f"Gender: {image_data['GenderText']}"),
                    html.P(f"Age Range: {image_data['MinAge']} - {image_data['MaxAge']}"),
                    html.P(f"Upload Time: {pd.to_datetime(image_data['Timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
                    #TODO: from base dataset also country, browser, os 
                    #TODO: sum uploads, sum token received,
                ])
            ], style={'display': 'flex', 'alignItems': 'start'})
        ])

    def create_generations_table(self, generations_df):
        """Create a table showing all generations using this input image."""
        if len(generations_df) == 0:
            return html.Div("No generations found for this image.")
        
        return html.Div([
            html.H3(f"Generations ({len(generations_df)} total)"),
            html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Preview", style=TABLE_HEADER_STYLE),
                        html.Th("Style", style=TABLE_HEADER_STYLE),
                        html.Th("Prompt", style=TABLE_HEADER_STYLE),
                        html.Th("Session", style=TABLE_HEADER_STYLE),
                        html.Th("Country", style=TABLE_HEADER_STYLE),
                        html.Th("Language", style=TABLE_HEADER_STYLE),
                        html.Th("Browser", style=TABLE_HEADER_STYLE),
                        html.Th("Generation Time", style=TABLE_HEADER_STYLE)
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(
                            html.Img(
                                src=os.path.join("/cache", row['GeneratedImagePath']),
                                style={'maxWidth': '100px', 'cursor': 'pointer'},
                                id={'type': 'preview-image', 'index': f"gen-{row['GenerationId']}"},
                                title='Click to enlarge'
                            ),
                            style=TABLE_CELL_STYLE
                        ),
                        html.Td(row['Style'], style=TABLE_CELL_STYLE),
                        html.Td(row['Prompt'], style=TABLE_CELL_STYLE),
                        html.Td(row['Session'], style=TABLE_CELL_STYLE),
                        html.Td(row['Country'], style=TABLE_CELL_STYLE),
                        html.Td(row['Language'], style=TABLE_CELL_STYLE),
                        html.Td(row['Browser'], style=TABLE_CELL_STYLE),
                       html.Td(pd.to_datetime(row['Timestamp']).strftime('%Y-%m-%d %H:%M:%S'), style=TABLE_CELL_STYLE)
                    ]) for _, row in generations_df.iterrows()
                ])
            ], style=TABLE_STYLE)
        ])
    
    def register_callbacks(self):
        """Register callbacks for the Generation Details tab."""
        logger.info("Registering Generation Details tab callbacks")
        @self.app.callback(
            [
                Output('adhoc_image-modal', 'style'),
                Output('adhoc_modal-image', 'src'),
                Output('adhoc_current-image-src', 'data')
            ],
            [
                Input({'type': 'preview-image', 'index': ALL}, 'n_clicks'),
                Input('adhoc_image-modal', 'n_clicks')
            ],
            [
                State({'type': 'preview-image', 'index': ALL}, 'src'),
                State('adhoc_current-image-src', 'data')
            ]
        )
        def toggle_image_modal(image_clicks, modal_clicks, image_srcs, current_src):
            """Handle image preview clicks to show/hide modal."""
            logger.debug("Image modal callback triggered")
            triggered = ctx.triggered_id
            modal_style = {
                'display': 'none',
                'position': 'fixed',
                'zIndex': 1000,
                'left': 0,
                'top': 0,
                'width': '100%',
                'height': '100%',
                'backgroundColor': 'rgba(0,0,0,0.9)',
                'cursor': 'pointer'
            }
            
            # If modal background was clicked, hide it
            if triggered == 'adhoc_image-modal':
                logger.debug("Modal background clicked, hiding modal")
                return modal_style, None, None
            
            # If an image was clicked (and not the search button)
            if triggered and isinstance(triggered, dict) and triggered.get('type') == 'preview-image' and any(clicks for clicks in image_clicks):
                logger.debug("Image preview clicked, showing modal")
                # Show modal
                modal_style['display'] = 'block'
                
                # Find which image was clicked and get its source
                for i, clicks in enumerate(image_clicks):
                    if clicks:
                        logger.debug(f"Displaying image: {image_srcs[i]}")
                        return modal_style, image_srcs[i], image_srcs[i]
            
            # Default - no change
            return modal_style, current_src, current_src

        @self.app.callback(
            [
                Output('adhoc_search-results', 'children'),
                Output('adhoctable', 'children')
            ],
            [Input('adhoc_search-button', 'n_clicks')],
            [State('adhoc_image_search', 'value')]
        )
        def search_image(n_clicks, search_value):
            """Handle image search and display results."""
            logger.debug(f"Image search triggered for value: {search_value}")
            if n_clicks == 0:
                logger.debug("Initial callback, no search performed")
                return None, None
            
            if not search_value:
                logger.debug("No search value provided")
                return "Please enter an Input ID or SHA1 hash.", None
            
            # Search for the image
            logger.info(f"Searching for image with ID/SHA1/Session: {search_value}")
            image_data, generations_df = self.data_manager.get_related_images(search_value)
            
            if image_data is None:
                logger.info("No image found with provided ID/SHA1")
                return "No image found with the provided ID or SHA1.", None
            
            logger.info(f"Found image with {len(generations_df)} generations")
            return (
                self.create_image_details(image_data),
                self.create_generations_table(generations_df)
            )
