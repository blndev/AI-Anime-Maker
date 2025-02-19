from dash import html, dcc, Input, Output
import dash
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from ..styles import HEADER_STYLE, PLOTLY_TEMPLATE, LAYOUT_THEME

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
