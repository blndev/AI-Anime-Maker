from dash import html, dcc, Input, Output
import dash
from ..diagrams_generations import create_style_usage_chart
from ..styles import HEADER_STYLE

class GenerationDetailsTab:
    def __init__(self, data_manager):
        """Initialize the Generation Details tab with a DataManager instance."""
        self.data_manager = data_manager
        
    def create_layout(self, initial_start_date, initial_end_date):
        """Create the layout for the Generation Details tab."""
        return [
            # Style Usage Section
            html.Div([
                html.H2("Generation Style Usage", style=HEADER_STYLE),
                dcc.Graph(
                    id='style-usage-chart',
                    figure=create_style_usage_chart(
                        self.data_manager.get_style_usage(initial_start_date, initial_end_date)
                    )
                )
            ])
        ]
    
    def register_callbacks(self, app):
        """Register callbacks for the Generation Details tab."""
        @app.callback(
            Output('style-usage-chart', 'figure'),
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
            return create_style_usage_chart(style_data)
