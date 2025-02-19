from dash import html, dcc, Input, Output, State, callback
import dash
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from ..styles import (
    HEADER_STYLE, PLOTLY_TEMPLATE, LAYOUT_THEME, CONTENT_STYLE,
    SEARCH_CONTAINER_STYLE, SEARCH_INPUT_STYLE, SEARCH_BUTTON_STYLE,
    TABLE_STYLE, TABLE_HEADER_STYLE, TABLE_CELL_STYLE
)

class GenerationDetailsTab:
    def __init__(self, data_manager, app):
        """Initialize the Generation Details tab with a DataManager instance."""
        self.data_manager = data_manager
        self.app = app
        self.register_callbacks()

    def create_style_usage_chart(self, df, start_date=None, end_date=None):
        """Create pie chart showing generation style distribution with percentages."""
        # Create figure
        fig = go.Figure()
        
        if len(df) == 0:
            fig.update_layout(
                title='Generation Style Distribution (No data available)',
                template=PLOTLY_TEMPLATE,
                **LAYOUT_THEME,
                showlegend=False
            )
            return fig
        
        # Get style usage data with percentages
        style_data = df
        
        # Add pie chart
        fig.add_trace(go.Pie(
            labels=style_data['Style'],
            values=style_data['Percentage'],
            marker=dict(colors=px.colors.qualitative.Set3),  # Use a color set that works well for pie charts
            textinfo='label+percent',  # Show both style name and percentage
            hovertemplate="<br>".join([
                "Style: %{label}",
                "Percentage: %{value:.1f}%",
                "Count: %{customdata[0]}",
                "<extra></extra>"
            ]),
            customdata=style_data[['Count']].values
        ))
        
        # Update layout
        fig.update_layout(
            title='Generation Style Distribution',
            template=PLOTLY_TEMPLATE,
            **LAYOUT_THEME,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
        
    def create_layout(self, initial_start_date, initial_end_date):
        """Create the layout for the Generation Details tab."""
        return [
            # Search Section
            html.Div([
                html.H2("Search by Input ID or SHA1", style=HEADER_STYLE),
                html.Div([
                    dcc.Input(
                        id='image-search',
                        type='text',
                        placeholder='Enter Input ID or SHA1',
                        style={**SEARCH_INPUT_STYLE, 'width': '300px'}
                    ),
                    html.Button('Search', id='search-button', n_clicks=0, style=SEARCH_BUTTON_STYLE)
                ], style=SEARCH_CONTAINER_STYLE),
                
                # Results Section
                html.Div(id='search-results', style={'marginBottom': '30px'}),
                
                html.Div(id='generations-table', style={'marginBottom': '30px'})
            ], style=CONTENT_STYLE),

            # Style Usage Section
            html.Div([
                html.H2("Generation Style Usage", style=HEADER_STYLE),
                dcc.Graph(
                    id='generation_details_style_usage',
                    figure=self.create_style_usage_chart(
                        self.data_manager.get_style_usage(initial_start_date, initial_end_date)
                    )
                )
            ])
        ]

    def create_image_details(self, image_data):
        """Create a details panel for the input image."""
        return html.Div([
            html.H3("Image Details"),
            html.Div([
                html.Img(src=image_data['CachePath'], style={'maxWidth': '200px', 'marginRight': '20px'}),
                html.Div([
                    html.P(f"Input ID: {image_data['ID']}"),
                    html.P(f"SHA1: {image_data['SHA1']}"),
                    html.P(f"Face Detected: {image_data['Face']}"),
                    html.P(f"Gender: {image_data['Gender']}"),
                    html.P(f"Age Range: {image_data['MinAge']} - {image_data['MaxAge']}"),
                    html.P(f"Upload Time: {pd.to_datetime(image_data['Timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
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
                        html.Th("Generation Time", style=TABLE_HEADER_STYLE)
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(html.Img(src=row['GeneratedImagePath'], style={'maxWidth': '100px'}), style=TABLE_CELL_STYLE),
                        html.Td(row['Style'], style=TABLE_CELL_STYLE),
                        html.Td(row['Prompt'], style=TABLE_CELL_STYLE),
                        html.Td(pd.to_datetime(row['Timestamp']).strftime('%Y-%m-%d %H:%M:%S'), style=TABLE_CELL_STYLE)
                    ]) for _, row in generations_df.iterrows()
                ])
            ], style=TABLE_STYLE)
        ])
    
    def register_callbacks(self):
        """Register callbacks for the Generation Details tab."""
        @self.app.callback(
            [
                Output('search-results', 'children'),
                Output('generations-table', 'children')
            ],
            [Input('search-button', 'n_clicks')],
            [State('image-search', 'value')]
        )
        def search_image(n_clicks, search_value):
            """Handle image search and display results."""
            if n_clicks == 0:
                return None, None
            
            if not search_value:
                return "Please enter an Input ID or SHA1 hash.", None
            
            # Search for the image
            image_data, generations_df = self.data_manager.get_image_by_id_or_sha1(search_value)
            
            if image_data is None:
                return "No image found with the provided ID or SHA1.", None
            
            return (
                self.create_image_details(image_data),
                self.create_generations_table(generations_df)
            )

        @self.app.callback(
            Output('generation_details_style_usage', 'figure'),
            [
                Input('active-filters-store', 'data'),
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date')
            ]
        )
        def update_style_usage_chart(filters_data, start_date, end_date):
            """Update style usage chart based on active filters and date range."""
            # First prepare filtered data to update the internal state
            self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
            # Then get style usage data
            style_data = self.data_manager.get_style_usage(start_date, end_date)
            return self.create_style_usage_chart(style_data)
