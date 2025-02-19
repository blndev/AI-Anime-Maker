from dash import html, dcc, Input, Output
import dash
import os
import pandas as pd
import plotly.graph_objects as go
from ..styles import HEADER_STYLE, PLOTLY_TEMPLATE, LAYOUT_THEME

class ImageUploadAnalysisTab:
    def __init__(self, data_manager, cache_dir, app):
        """Initialize the Image Upload Analysis tab with a DataManager instance."""
        self.data_manager = data_manager
        self.cache_dir = cache_dir
        self.app = app
        self.register_callbacks()

    def create_image_uploads_timeline(self, df):
        """Create timeline of image uploads and generations aggregated by hour with local timezone."""
        # Create figure
        fig = go.Figure()
        
        if len(df) == 0:
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

    def create_top_uploaded_images_chart(self, df):
        """Create bar chart of most frequently uploaded images."""
        # Create figure with subplots: bar chart on top, image grid below
        fig = go.Figure()
        
        if len(df) == 0:
            fig.update_layout(
                title='Top 10 Most Frequently Uploaded Images (No data available)',
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
        
        # Add hover text with image details
        fig.update_traces(
            hovertemplate="<br>".join([
                "Input ID: %{x}",
                "Upload Count: %{y}",
                "SHA1: %{customdata[4]}",
                "Path: %{customdata[0]}",
                "Token: %{customdata[1]}",
                "Face: %{customdata[2]}",
                "Gender: %{customdata[3]}"
            ]),
            customdata=df[['CachePath', 'Token', 'Face', 'Gender', 'SHA1']].values
        )
        
        # Update layout
        fig.update_layout(
            title='Top 10 Most Frequently Uploaded Images',
            xaxis_title='Image ID',
            yaxis_title='Number of Uploads',
            template=PLOTLY_TEMPLATE,
            **LAYOUT_THEME
        )
        
        return fig

    def create_top_generated_images_chart(self, df):
        """Create bar chart of images used most for generations."""
        # Create figure
        fig = go.Figure()
        
        if len(df) == 0:
            fig.update_layout(
                title='Top 10 Most Generated From Images (No data available)',
                xaxis_title='Image SHA1',
                yaxis_title='Number of Generations',
                template=PLOTLY_TEMPLATE,
                showlegend=False
            )
            fig.update_layout(**LAYOUT_THEME)
            return fig
        
        # Add bar chart using SHA1 as x-axis labels
        fig.add_trace(go.Bar(
            x=df['SHA1'].apply(lambda x: f"SHA1: {x[:8]}..."),
            y=df['GenerationCount'],
            name='Generation Count',
            marker_color='#E74C3C'  # Red to match generation line in timeline
        ))
        
        # Add hover text with image details
        fig.update_traces(
            hovertemplate="<br>".join([
                "SHA1: %{x}",
                "Generations: %{y}",
                "Input ID: %{customdata[1]}",
                "Path: %{customdata[0]}",
                "Token: %{customdata[2]}",
                "Face: %{customdata[3]}",
                "Gender: %{customdata[4]}"
            ]),
            customdata=df[['CachePath', 'ID', 'Token', 'Face', 'Gender']].values
        )
        
        # Update layout
        fig.update_layout(
            title='Top 10 Most Generated From Images',
            xaxis_title='Image SHA1',
            yaxis_title='Number of Generations',
            template=PLOTLY_TEMPLATE,
            **LAYOUT_THEME
        )
        
        return fig
        
    def create_layout(self, initial_df, initial_top_images_df):
        """Create the layout for the Image Upload Analysis tab."""
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
                dcc.Graph(id='uploads_top_images', figure=self.create_top_uploaded_images_chart(initial_top_images_df)),
                # Image grid (updated via callback)
                html.Div(id='uploads_image_grid')
            ]),
            
            # Top Generated Images Section with Details
            html.Div([
                html.H2("Most Used for Generations", style=HEADER_STYLE),
                html.Div([
                    # Left column: Chart
                    html.Div([
                        dcc.Graph(
                            id='uploads_generated_images',
                            figure=self.create_top_generated_images_chart(self.data_manager.get_top_generated_images())
                        )
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    
                    # Right column: Details
                    html.Div([
                        html.H3("Image Details", style=HEADER_STYLE),
                        html.Div(id='uploads_image_details', children=[
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
    
    def register_callbacks(self):
        """Register callbacks for the Image Upload Analysis tab."""
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
            filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
            filtered_top_images_df = self.data_manager.get_top_uploaded_images()
            
            return [
                self.create_image_uploads_timeline(filtered_df),
                self.create_top_uploaded_images_chart(filtered_top_images_df),
                self.create_top_generated_images_chart(self.data_manager.get_top_generated_images())
            ]
        
        @self.app.callback(
            Output('uploads_image_grid', 'children'),
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
        
        @self.app.callback(
            Output('uploads_image_details', 'children'),
            [
                Input('uploads_generated_images', 'clickData'),
                Input('uploads_top_images', 'clickData')
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
            click_data = generation_click if trigger_id == 'uploads_generated_images' else upload_click
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
            if trigger_id == 'uploads_generated_images':
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
            count_label = "Generations" if trigger_id == 'uploads_generated_images' else "Uploads"
            count_value = image_data['GenerationCount'] if trigger_id == 'uploads_generated_images' else image_data['UploadCount']
            
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
