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

class GenerationDetailsTab:
    def __init__(self, data_manager, app):
        """Initialize the Generation Details tab with a DataManager instance."""
        logger.info("Initializing Generation Details tab")
        self.data_manager = data_manager
        self.app = app
        self.register_callbacks()
        logger.info("Generation Details tab initialized successfully")

    def create_style_usage_chart(self, df, start_date=None, end_date=None):
        """Create pie chart showing generation style distribution with percentages."""
        logger.debug(f"Creating style usage chart for date range: {start_date} to {end_date}")
        # Create figure
        fig = go.Figure()
        
        if len(df) == 0:
            logger.debug("No style usage data available")
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
            # Modal for full-size image view
            dcc.Store(id='current-image-src', data=None),
            html.Div(
                id='image-modal',
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
                        id='modal-image',
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

    
    def register_callbacks(self):
        """Register callbacks for the Generation Details tab."""
        logger.info("Registering Generation Details tab callbacks")

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
            logger.debug(f"Updating style usage chart for date range: {start_date} to {end_date}")
            # First prepare filtered data to update the internal state
            self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
            # Then get style usage data
            style_data = self.data_manager.get_style_usage(start_date, end_date)
            return self.create_style_usage_chart(style_data)
            return self.create_style_usage_chart(style_data)
