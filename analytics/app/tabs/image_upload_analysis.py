from dash import html, dcc, Input, Output
import dash
import os
import pandas as pd
from ..diagrams_uploads import (
    create_image_uploads_timeline,
    create_top_uploaded_images_chart,
    create_top_generated_images_chart
)
from ..styles import HEADER_STYLE

class ImageUploadAnalysisTab:
    def __init__(self, data_manager, cache_dir):
        """Initialize the Image Upload Analysis tab with a DataManager instance."""
        self.data_manager = data_manager
        self.cache_dir = cache_dir
        
    def create_layout(self, initial_df, initial_top_images_df):
        """Create the layout for the Image Upload Analysis tab."""
        return [
            # Image Uploads Timeline
            html.Div([
                html.H2("Image Upload Patterns", style=HEADER_STYLE),
                dcc.Graph(id='image-uploads-timeline', figure=create_image_uploads_timeline(initial_df))
            ]),
            
            # Top Images Section
            html.Div([
                html.H2("Most Uploaded Images", style=HEADER_STYLE),
                # Bar chart showing upload counts
                dcc.Graph(id='top-images-chart', figure=create_top_uploaded_images_chart(initial_top_images_df)),
                # Image grid (updated via callback)
                html.Div(id='image-grid')
            ]),
            
            # Top Generated Images Section with Details
            html.Div([
                html.H2("Most Used for Generations", style=HEADER_STYLE),
                html.Div([
                    # Left column: Chart
                    html.Div([
                        dcc.Graph(
                            id='top-generated-images-chart',
                            figure=create_top_generated_images_chart(self.data_manager.get_top_generated_images())
                        )
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
    
    def register_callbacks(self, app):
        """Register callbacks for the Image Upload Analysis tab."""
        @app.callback(
            [
                Output('image-uploads-timeline', 'figure'),
                Output('top-images-chart', 'figure'),
                Output('top-generated-images-chart', 'figure')
            ],
            [
                Input('active-filters-store', 'data'),
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date')
            ]
        )
        def update_image_charts(filters_data, start_date, end_date):
            """Update image analysis charts."""
            filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
            filtered_top_images_df = self.data_manager.get_top_uploaded_images()
            
            return [
                create_image_uploads_timeline(filtered_df),
                create_top_uploaded_images_chart(filtered_top_images_df),
                create_top_generated_images_chart(self.data_manager.get_top_generated_images())
            ]
        
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
            self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
            top_images_df = self.data_manager.get_top_uploaded_images()
            
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
            
            # Get the selected image details from the click data
            selected_id = click_data['points'][0]['x']
            selected_path = click_data['points'][0]['customdata'][0]
            selected_token = click_data['points'][0]['customdata'][1]
            selected_face = click_data['points'][0]['customdata'][2]
            selected_gender = click_data['points'][0]['customdata'][3]
            
            # Get details based on which chart was clicked
            if trigger_id == 'top-generated-images-chart':
                # Extract SHA1 from "SHA1: {sha1}..." format
                raw_sha1 = selected_id.split(': ')[1].split('...')[0]
                df_details = self.data_manager.get_top_generated_images()
                filtered_details = df_details[df_details['SHA1'].str.contains(raw_sha1, regex=False)]
            else:
                # Extract ID from "ID: {id}" format
                raw_id = selected_id.split(': ')[1]
                df_details = self.data_manager.get_top_uploaded_images()
                filtered_details = df_details[df_details['ID'].astype(str) == raw_id]
            
            if len(filtered_details) == 0:
                return html.Div("Image details not found", style={
                    'color': '#95A5A6',
                    'fontStyle': 'italic',
                    'textAlign': 'center',
                    'marginTop': '20px'
                })
            
            image_data = filtered_details.iloc[0]
            
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
