"""
Geographic Distribution tab for analytics dashboard.
Handles geographic data visualization and filter management.
"""
from dash import html, dcc, Input, Output
import dash
import plotly.express as px
import pandas as pd
from ..styles import (
    HEADER_STYLE, NO_DATA_STYLE,
    FILTER_TAG_STYLE, PLATFORM_FILTER_STYLE, LANGUAGE_FILTER_STYLE,
    PLOTLY_TEMPLATE, LAYOUT_THEME
)

class GeographicDistributionTab:
    def __init__(self, data_manager, app):
        """Initialize the Geographic Distribution tab with a DataManager instance."""
        self.data_manager = data_manager
        self.app = app
        self.register_callbacks()

    def create_language_chart(self, df, selected_language=None):
        """Create language distribution chart."""
        fig = px.bar(
            pd.DataFrame({'Language': [], 'Count': []}),
            x='Language',
            y='Count',
            title="Top 10 Languages",
            labels={'Language': 'Language', 'Count': 'Number of Sessions'},
            template=PLOTLY_TEMPLATE
        )
        
        if len(df) == 0:
            fig.update_layout(
                title="Top 10 Languages (No data available)",
                **LAYOUT_THEME,
                showlegend=False
            )
            return fig
        
        language_counts = df['Language'].fillna('Unknown').value_counts().head(10).reset_index()
        language_counts.columns = ['Language', 'Count']
        
        fig = px.bar(
            language_counts,
            x='Language',
            y='Count',
            title="Top 10 Languages",
            labels={'Language': 'Language', 'Count': 'Number of Sessions'},
            template=PLOTLY_TEMPLATE
        )
        fig.update_layout(
            **LAYOUT_THEME,
            clickmode='event',
            dragmode='select'
        )
        
        # Highlight selected language if any
        if selected_language:
            fig.update_traces(
                marker_color=[
                    '#1f77b4' if x == selected_language else '#7fdbff' 
                    for x in language_counts['Language']
                ]
            )
        return fig

    def create_continent_chart(self, df, selected_continent=None):
        """Create continent distribution chart."""
        fig = px.bar(
            pd.DataFrame({'Continent': [], 'Count': []}),
            x='Continent',
            y='Count',
            title="Geographic Distribution by Continent (Click to Filter)",
            labels={'Continent': 'Continent', 'Count': 'Number of Sessions'},
            template=PLOTLY_TEMPLATE
        )
        
        if len(df) == 0:
            fig.update_layout(
                title="Geographic Distribution by Continent (No data available)",
                **LAYOUT_THEME,
                showlegend=False
            )
            return fig
        
        continent_counts = df['Continent'].fillna('Unknown').value_counts().reset_index()
        continent_counts.columns = ['Continent', 'Count']
        
        fig = px.bar(
            continent_counts,
            x='Continent',
            y='Count',
            title="Geographic Distribution by Continent (Click to Filter)",
            labels={'Continent': 'Continent', 'Count': 'Number of Sessions'},
            template=PLOTLY_TEMPLATE
        )
        fig.update_layout(
            **LAYOUT_THEME,
            clickmode='event',
            dragmode='select'  # Enable selection mode
        )
        # Highlight selected continent if any
        if selected_continent:
            fig.update_traces(
                marker_color=[
                    '#1f77b4' if x == selected_continent else '#7fdbff' 
                    for x in continent_counts['Continent']
                ]
            )
        return fig

    def create_country_chart(self, df, selected_continent=None, selected_country=None):
        """Create country distribution chart."""
        fig = px.bar(
            pd.DataFrame({'Country': [], 'Count': []}),
            x='Country',
            y='Count',
            title="Top 10 Countries by Usage (Click to Filter)",
            labels={'Country': 'Country', 'Count': 'Number of Sessions'},
            template=PLOTLY_TEMPLATE
        )
        
        if len(df) == 0:
            fig.update_layout(
                title="Top 10 Countries by Usage (No data available)",
                **LAYOUT_THEME,
                showlegend=False
            )
            return fig
        
        # Filter by continent if selected
        if selected_continent:
            df = df[df['Continent'] == selected_continent]
        
        country_counts = df['Country'].fillna('Unknown').value_counts().head(10).reset_index()
        country_counts.columns = ['Country', 'Count']
        
        fig = px.bar(
            country_counts,
            x='Country',
            y='Count',
            title=f"Top 10 Countries by Usage{' in ' + selected_continent if selected_continent else ''} (Click to Filter)",
            labels={'Country': 'Country', 'Count': 'Number of Sessions'},
            template=PLOTLY_TEMPLATE
        )
        fig.update_layout(
            **LAYOUT_THEME,
            clickmode='event',
            dragmode='select'  # Enable selection mode
        )
        # Highlight selected country if any
        if selected_country:
            fig.update_traces(
                marker_color=[
                    '#1f77b4' if x == selected_country else '#7fdbff' 
                    for x in country_counts['Country']
                ]
            )
        return fig

    def create_city_chart(self, df, selected_continent=None, selected_country=None):
        """Create city distribution chart."""
        fig = px.bar(
            pd.DataFrame({'City': [], 'Count': []}),
            x='City',
            y='Count',
            title="Top 10 Cities by Usage",
            labels={'City': 'City', 'Count': 'Number of Sessions'},
            template=PLOTLY_TEMPLATE
        )
        
        if len(df) == 0:
            fig.update_layout(
                title="Top 10 Cities by Usage (No data available)",
                **LAYOUT_THEME,
                showlegend=False
            )
            return fig
        
        # Apply filters
        if selected_continent:
            df = df[df['Continent'] == selected_continent]
        if selected_country:
            df = df[df['Country'] == selected_country]
        
        city_counts = df['City'].fillna('Unknown').value_counts().head(10).reset_index()
        city_counts.columns = ['City', 'Count']
        
        fig = px.bar(
            city_counts,
            x='City',
            y='Count',
            title="Top 10 Cities by Usage",
            labels={'City': 'City', 'Count': 'Number of Sessions'},
            template=PLOTLY_TEMPLATE
        )
        fig.update_layout(**LAYOUT_THEME)
        return fig
        
    def create_layout(self, initial_df):
        """Create the layout for the Geographic Distribution tab."""
        active_filters = self.data_manager.get_active_filters()
        return [
            # Geographic Distribution Section
            html.Div([
                html.H2("Geographic Distribution", style=HEADER_STYLE),
                
                # Continent and Country charts side by side
                html.Div([
                    html.Div([
                        dcc.Graph(
                            id='geo_continent',
                            figure=self.create_continent_chart(initial_df, 
                                selected_continent=active_filters.get('continent'))
                        )
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(
                            id='geo_country',
                            figure=self.create_country_chart(initial_df,
                                selected_continent=active_filters.get('continent'),
                                selected_country=active_filters.get('country'))
                        )
                    ], style={'width': '50%', 'display': 'inline-block'})
                ]),
                
                # City chart full width
                html.Div([
                    dcc.Graph(
                        id='geo_city',
                        figure=self.create_city_chart(initial_df,
                            selected_continent=active_filters.get('continent'),
                            selected_country=active_filters.get('country'))
                    )
                ])
            ]),
            
            # Language Distribution Section
            html.Div([
                html.H2("Language Distribution", style=HEADER_STYLE),
                html.Div([
                    dcc.Graph(
                        id='geo_language',
                        figure=self.create_language_chart(initial_df,
                            selected_language=active_filters.get('language'))
                    )
                ])
            ])
        ]
    
    def register_callbacks(self):
        """Register callbacks for the Geographic Distribution tab."""
        @self.app.callback(
            [
                Output('geo_continent', 'figure'),
                Output('geo_country', 'figure'),
                Output('geo_city', 'figure'),
                Output('geo_language', 'figure')
            ],
            [
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date'),
                Input('geo_continent', 'clickData'),
                Input('geo_country', 'clickData'),
                Input('geo_language', 'clickData'),
                Input('reset-geo-filters', 'n_clicks')
            ]
        )
        def update_charts(start_date, end_date, continent_click, country_click, 
                         language_click, reset_clicks):
            """Update all charts based on date range and filter selections."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return dash.no_update
            
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            # Handle filter updates
            if trigger_id == 'reset-geo-filters':
                self.data_manager.reset_filters()
            elif trigger_id == 'geo_continent' and continent_click:
                self.data_manager.add_filter('continent', continent_click['points'][0]['x'])
            elif trigger_id == 'geo_country' and country_click:
                self.data_manager.add_filter('country', country_click['points'][0]['x'])
            elif trigger_id == 'geo_language' and language_click:
                self.data_manager.add_filter('language', language_click['points'][0]['x'])
            
            # Get filtered data
            filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date)
            
            # Get active filters
            active_filters = self.data_manager.get_active_filters()
            
            # Update all charts with active filters
            return [
                self.create_continent_chart(filtered_df, selected_continent=active_filters.get('continent')),
                self.create_country_chart(filtered_df, 
                                        selected_continent=active_filters.get('continent'),
                                        selected_country=active_filters.get('country')),
                self.create_city_chart(filtered_df,
                                     selected_continent=active_filters.get('continent'),
                                     selected_country=active_filters.get('country')),
                self.create_language_chart(filtered_df, selected_language=active_filters.get('language'))
            ]
        
        @self.app.callback(
            Output('active-filters', 'children'),
            [Input('date-range', 'start_date'),
             Input('date-range', 'end_date'),
             Input('geo_continent', 'clickData'),
             Input('geo_country', 'clickData'),
             Input('geo_language', 'clickData'),
             Input('reset-geo-filters', 'n_clicks')]
        )
        def update_active_filters_display(*_):
            """Update the active filters display."""
            active_filters = self.data_manager.get_active_filters()
            
            if not active_filters:
                return [html.Div("No filters active", style=NO_DATA_STYLE)]
            
            filters = []
            
            # Geographic filters
            if active_filters.get('continent'):
                filters.append(
                    html.Div([
                        html.Strong("Continent: "),
                        html.Span(active_filters['continent'])
                    ], style=FILTER_TAG_STYLE)
                )
            
            if active_filters.get('country'):
                filters.append(
                    html.Div([
                        html.Strong("Country: "),
                        html.Span(active_filters['country'])
                    ], style=FILTER_TAG_STYLE)
                )
            
            # Platform filters
            if active_filters.get('os'):
                filters.append(
                    html.Div([
                        html.Strong("OS: "),
                        html.Span(active_filters['os'])
                    ], style=PLATFORM_FILTER_STYLE)
                )
            
            if active_filters.get('browser'):
                filters.append(
                    html.Div([
                        html.Strong("Browser: "),
                        html.Span(active_filters['browser'])
                    ], style=PLATFORM_FILTER_STYLE)
                )
            
            # Language filter
            if active_filters.get('language'):
                filters.append(
                    html.Div([
                        html.Strong("Language: "),
                        html.Span(active_filters['language'])
                    ], style=LANGUAGE_FILTER_STYLE)
                )
            
            return filters
