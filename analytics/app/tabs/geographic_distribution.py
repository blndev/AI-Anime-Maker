from dash import html, dcc, Input, Output
import dash
from ..diagrams_origin import (
    create_language_chart, create_continent_chart,
    create_country_chart, create_city_chart
)
from ..styles import HEADER_STYLE

class GeographicDistributionTab:
    def __init__(self, data_manager):
        """Initialize the Geographic Distribution tab with a DataManager instance."""
        self.data_manager = data_manager
        
    def create_layout(self, initial_df):
        """Create the layout for the Geographic Distribution tab."""
        return [
            # Language Distribution Section
            html.Div([
                html.H2("Language Distribution", style=HEADER_STYLE),
                dcc.Graph(id='language-chart', figure=create_language_chart(initial_df))
            ]),
            
            # Geographic Distribution Section
            html.Div([
                html.H2("Geographic Distribution", style=HEADER_STYLE),
                html.Div([
                    html.Div([
                        dcc.Graph(id='continent-chart', figure=create_continent_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='country-chart', figure=create_country_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'})
                ]),
                html.Div([
                    dcc.Graph(id='city-chart', figure=create_city_chart(initial_df))
                ])
            ])
        ]
    
    def register_callbacks(self, app):
        """Register callbacks for the Geographic Distribution tab."""
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
            
            # Get filtered data excluding geographic filters
            geo_filters = {k: v for k, v in filters_data.items() if k not in ['continent', 'country']}
            filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, geo_filters)
            
            # Create updated figures with filtered data
            continent_fig = create_continent_chart(filtered_df, filters_data.get('continent'))
            country_fig = create_country_chart(filtered_df, filters_data.get('continent'), filters_data.get('country'))
            city_fig = create_city_chart(filtered_df, filters_data.get('continent'), filters_data.get('country'))
            
            return continent_fig, country_fig, city_fig
        
        @app.callback(
            Output('language-chart', 'figure'),
            [
                Input('active-filters-store', 'data'),
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date')
            ]
        )
        def update_language_chart(filters_data, start_date, end_date):
            """Update language chart based on active filters and date range."""
            filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
            return create_language_chart(filtered_df)
