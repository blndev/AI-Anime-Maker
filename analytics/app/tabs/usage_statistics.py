from dash import html, dcc, Input, Output
import dash
from ..diagrams_usage import (
    create_sessions_timeline, create_os_chart, create_browser_chart,
    create_mobile_pie, create_generation_status_chart
)
from ..styles import HEADER_STYLE

class UsageStatisticsTab:
    def __init__(self, data_manager):
        """Initialize the Usage Statistics tab with a DataManager instance."""
        self.data_manager = data_manager
        
    def create_layout(self, initial_df):
        """Create the layout for the Usage Statistics tab."""
        return [
            # Sessions Timeline
            html.Div([
                dcc.Graph(id='timeline-chart', figure=create_sessions_timeline(initial_df))
            ]),
            
            # Platform Statistics Section
            html.Div([
                html.H2("Platform Statistics", style=HEADER_STYLE),
                html.Div([
                    html.Div([
                        dcc.Graph(id='os-chart', figure=create_os_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='browser-chart', figure=create_browser_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'})
                ]),
                html.Div([
                    html.Div([
                        dcc.Graph(id='mobile-chart', figure=create_mobile_pie(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='generation-status-chart', figure=create_generation_status_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'})
                ])
            ])
        ]
    
    def register_callbacks(self, app):
        """Register callbacks for the Usage Statistics tab."""
        @app.callback(
            [
                Output('timeline-chart', 'figure'),
                Output('os-chart', 'figure'),
                Output('browser-chart', 'figure'),
                Output('mobile-chart', 'figure'),
                Output('generation-status-chart', 'figure')
            ],
            [
                Input('active-filters-store', 'data'),
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date')
            ]
        )
        def update_usage_charts(filters_data, start_date, end_date):
            """Update all usage statistics charts."""
            filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
            
            return [
                create_sessions_timeline(filtered_df),
                create_os_chart(filtered_df),
                create_browser_chart(filtered_df),
                create_mobile_pie(filtered_df),
                create_generation_status_chart(filtered_df)
            ]
