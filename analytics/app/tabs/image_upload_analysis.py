from dash import html, dcc, Input, Output
import dash
import os
import pandas as pd
import plotly.graph_objects as go
import logging

# Set up logging
logger = logging.getLogger(__name__)
from ..styles import HEADER_STYLE, PLOTLY_TEMPLATE, LAYOUT_THEME

class ImageUploadAnalysisTab:
    def __init__(self, data_manager, cache_dir, app):
        """Initialize the Image Upload Analysis tab with a DataManager instance."""
        logger.info("Initializing Image Upload Analysis tab")
        self.data_manager = data_manager
        self.cache_dir = cache_dir
        self.app = app
        self.register_callbacks()
        logger.info("Image Upload Analysis tab initialized successfully")

    def create_image_uploads_timeline(self, df):
        """Create timeline of image uploads and generations aggregated by hour with local timezone."""
        logger.debug("Creating image uploads timeline chart")
        # Create figure
        fig = go.Figure()
        
        if len(df) == 0:
            logger.debug("No data available for timeline")
            fig.update_layout(
                title='Activity per Hour (No data available)',
                xaxis_title='Date & Time',
                yaxis_title='Count',
                template=PLOTLY_TEMPLATE,
                showlegend=False
            )
            fig.update_layout(**LAYOUT_THEME)
            return fig
        
        # Create a copy of the dataframe
        data = df.copy()
        
        # Get timezone info from the timestamp column
        tz = data['Timestamp'].dt.tz
        tz_name = str(tz) if tz else 'Local'
        
        # Group by hour and aggregate metrics
        data['Hour'] = data['Timestamp'].dt.floor('H')
        hourly_data = data.groupby('Hour').agg({
            'ImageUploads': 'sum',
            'GenerationCount': 'sum',
            'Session': 'nunique'  # Count unique sessions
        }).reset_index()
        hourly_data = hourly_data.rename(columns={'Session': 'SessionCount'})
        
        # Create figure
        fig = go.Figure()
        
        # Add uploads bars
        fig.add_trace(
            go.Bar(
                x=hourly_data['Hour'],
                y=hourly_data['ImageUploads'],
                name='Uploads',
                marker_color='#4B89DC',
                hovertemplate="<br>".join([
                    "Time: %{x}",
                    "Total Uploads: %{y}",
                    "<extra></extra>"
                ])
            )
        )
        
        # Add generations line
        fig.add_trace(
            go.Scatter(
                x=hourly_data['Hour'],
                y=hourly_data['GenerationCount'],
                name='Generations',
                line=dict(color='#E74C3C', width=2),
                hovertemplate="<br>".join([
                    "Time: %{x}",
                    "Total Generations: %{y}",
                    "<extra></extra>"
                ])
            )
        )
        
        # Add sessions line
        fig.add_trace(
            go.Scatter(
                x=hourly_data['Hour'],
                y=hourly_data['SessionCount'],
                name='New Sessions',
                line=dict(color='#2ECC71', width=2, dash='dot'),
                hovertemplate="<br>".join([
                    "Time: %{x}",
                    "New Sessions: %{y}",
                    "<extra></extra>"
                ])
            )
        )
        
        # Update layout
        fig.update_layout(
            title=f'Activity per Hour ({tz_name})',
            xaxis_title=f'Date & Time ({tz_name})',
            yaxis_title='Count',
            template=PLOTLY_TEMPLATE,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'  # Show all values for the same x coordinate
        )
        
        fig.update_layout(**LAYOUT_THEME)
        return fig

    def _add_image_details_hover(self, fig, df):
        # Add hover text with image details
        fig.update_traces(
            #todo: check how to integrate an image "<img src=""%{customdata[6]}"" style=""width:50px;height:50px;"">" + 
            hovertemplate="<br>".join([
                "Input ID: %{x}",
                "Upload Count: %{y}",
                "SHA1: %{customdata[0]}",
                "Path: %{customdata[1]}",
                "Token: %{customdata[2]}",
                "Face: %{customdata[3]}",
                "Gender: %{customdata[4]}",
                "Age: %{customdata[5]}"
            ]),
            customdata=df[['SHA1', 'CachePath', 'Token', 'Face', 'GenderText', 'AgeSpan']].values
        )

    def create_top_uploaded_images_chart(self, df):
        """Create bar chart of most frequently uploaded images."""
        logger.debug("Creating top uploaded images chart")
        # Create figure with subplots: bar chart on top, image grid below
        fig = go.Figure()
        
        if len(df) == 0:
            fig.update_layout(
                title='Top 10 - Most Frequently Uploaded Images (No data available)',
                xaxis_title='Image ID',
                yaxis_title='Number of Uploads',
                template=PLOTLY_TEMPLATE,
                showlegend=False
            )
            fig.update_layout(**LAYOUT_THEME)
            return fig
        
        # Add bar chart using ID as x-axis labels with required format for click handling
        fig.add_trace(go.Bar(
            x=df['ID'].astype(str).apply(lambda x: f"ID: {x}"),
            y=df['UploadCount'],
            name='Upload Count',
            marker_color='#4B89DC'
        ))

        self._add_image_details_hover(fig, df)

        # Update layout
        fig.update_layout(
            title='Top 10 - Most Frequently Uploaded Images',
            xaxis_title='Image ID',
            yaxis_title='Number of Uploads',
            template=PLOTLY_TEMPLATE,
            **LAYOUT_THEME
        )
        
        return fig

    def create_top_used_images_chart(self, df):
        """Create bar chart of images used most for generations."""
        logger.debug("Creating top generated images chart")
        # Create figure
        fig = go.Figure()
        
        if len(df) == 0:
            fig.update_layout(
                title='Top 10 - Most used for Generation (No data available)',
                xaxis_title='Image SHA1',
                yaxis_title='Number of Generations',
                template=PLOTLY_TEMPLATE,
                showlegend=False
            )
            fig.update_layout(**LAYOUT_THEME)
            return fig
        
        # Add bar chart using SHA1 as x-axis labels
        fig.add_trace(go.Bar(
            x=df['ID'].apply(lambda x: f"ID: {x}"),
            y=df['GenerationCount'],
            name='Generation Count',
            marker_color='#E74C3C'  #TODO: move color to styles (Red to match generation line in timeline)
        ))
        
        # Add hover text with image details
        self._add_image_details_hover(fig, df)

        # Update layout
        fig.update_layout(
            title='Top 10 - Most used for Generation',
            xaxis_title='Image SHA1',
            yaxis_title='Number of Generations',
            template=PLOTLY_TEMPLATE,
            **LAYOUT_THEME
        )
        
        return fig
        
    def create_layout(self, initial_df, initial_top_uploaded_images_df, initial_top_used_images_df):
        """Create the layout for the Image Upload Analysis tab."""
        logger.info("Creating Image Upload Analysis tab layout")
        return [
            # Image Uploads Timeline
            html.Div([
                html.H2("Image Upload Patterns", style=HEADER_STYLE),
                dcc.Graph(id='uploads_timeline', figure=self.create_image_uploads_timeline(initial_df))
            ]),
            
            # Top Images Section
            html.Div([
                html.H2("Most Uploaded Images", style=HEADER_STYLE),
                # Bar chart showing upload counts
                dcc.Graph(id='uploads_top_images', figure=self.create_top_uploaded_images_chart(initial_top_uploaded_images_df)),
            ]),
            
            # Top Generated Images Section with Details
            html.Div([
                html.H2("Most Used for Generations", style=HEADER_STYLE),
                html.Div([
                    # Left column: Chart
                    html.Div([
                        dcc.Graph(
                            id='uploads_generated_images',
                            figure=self.create_top_used_images_chart(initial_top_used_images_df)
                        )
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    
                    # Right column: Details
                    html.Div([
                        html.H3("Image Details", style=HEADER_STYLE),
                        html.Div(id='uploads_image_details', children=[
                            html.Div("Select an image to view details", style={
                                'color': '#95A5A6', #TODO: move style to styles
                                'fontStyle': 'italic',
                                'textAlign': 'center',
                                'marginTop': '20px'
                            })
                        ])
                    ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'})
                ])
            ])
        ]
    
    def register_callbacks(self):
        """Register callbacks for the Image Upload Analysis tab."""
        logger.info("Registering Image Upload Analysis tab callbacks")
        @self.app.callback(
            [
                Output('uploads_timeline', 'figure'),
                Output('uploads_top_images', 'figure'),
                Output('uploads_generated_images', 'figure')
            ],
            [
                Input('active-filters-store', 'data'),
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date')
            ]
        )
        def update_image_charts(filters_data, start_date, end_date):
            """Update image analysis charts."""
            logger.debug(f"Updating image charts for date range: {start_date} to {end_date}")
            try:
                filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
                filtered_top_uploaded_images_df = self.data_manager.get_top_uploaded_images()
                filtered_top_used_images_df = self.data_manager.get_top_used_images()
                
                logger.info(f"Retrieved filtered dataset with {len(filtered_df)} records")
                logger.debug(f"Retrieved {len(filtered_top_uploaded_images_df)} top uploaded images")
                logger.debug(f"Retrieved {len(filtered_top_used_images_df)} top used images")
                
                return [
                    self.create_image_uploads_timeline(filtered_df),
                    self.create_top_uploaded_images_chart(filtered_top_uploaded_images_df),
                    self.create_top_used_images_chart(filtered_top_used_images_df)
                ]
            except Exception as e:
                logger.error(f"Error updating image charts: {str(e)}")
                raise
        
        
        @self.app.callback(
            Output('uploads_image_details', 'children'),
            [
                Input('uploads_generated_images', 'clickData'),
                Input('uploads_top_images', 'clickData')
            ]
        )
        def update_image_details(generation_click, upload_click):
            """Update the details display when a bar in either chart is clicked."""
            logger.debug("Image details callback triggered")
            try:
                # Use the most recent click data
                ctx = dash.callback_context
                if not ctx.triggered:
                    logger.debug("No click data available")
                    return html.Div("Select an image to view details", style={
                        'color': '#95A5A6', #TODO: add color or style to styles files
                        'fontStyle': 'italic',
                        'textAlign': 'center',
                        'marginTop': '20px'
                    })
            
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                logger.debug(f"Triggered by: {trigger_id}")
                
                click_data = generation_click if trigger_id == 'uploads_generated_images' else upload_click
                if not click_data or not click_data.get('points'):
                    logger.debug("No valid click data points")
                    return html.Div("Select an image to view details", style={
                        'color': '#95A5A6',#TODO: add color or style to styles files
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
                
                logger.debug(f"Selected image ID: {selected_id}")
            
                # Extract ID from "ID: {id}" format
                raw_id = selected_id.split(': ')[1]
                image_data = self.data_manager.get_image_by_id_or_sha1(raw_id)
                #filtered_details = df_details[df_details['ID'].astype(str) == raw_id]
                logger.debug(f"Retrieved upload details for ID: {raw_id}")
            
                if len(image_data) == 0:
                    logger.warning("No details found for selected image")
                    return html.Div("Image details not found", style={
                        'color': '#95A5A6', #TODO: move color or style to styles files
                        'fontStyle': 'italic',
                        'textAlign': 'center',
                        'marginTop': '20px'
                    })
                
                logger.info(f"Displaying details for image with ID {raw_id}")
            
                details = [
                html.Div([
                    html.Img(
                        #FIXME: path calculation could be wrong
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
                        html.Span(image_data['GenderText'] if pd.notna(image_data['Gender']) else 'N/A')
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Strong("Age Range: "),
                        html.Span(image_data['AgeSpan'] if pd.notna(image_data['AgeSpan']) else 'N/A')
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Strong(f"Uploads for this File: "),
                        html.Span(str(image_data["UploadCount"]))
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Strong(f"Generations for this File: "),
                        html.Span(str(image_data["GenerationCount"]))
                    ], style={'margin': '5px 0'})
                ], style={
                    'backgroundColor': '#2C3E50',
                    'padding': '15px',
                    'borderRadius': '8px',
                    'margin': '10px'
                })
            ]
            
                return details
            except Exception as e:
                logger.error(f"Error updating image details: {str(e)}")
                raise
