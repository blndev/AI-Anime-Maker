"""
Geographic Distribution tab for analytics dashboard.
Handles geographic data visualization and filter management.
"""
from dash import html, dcc, Input, Output
import dash
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

# Set up logging
logger = logging.getLogger(__name__)
from ..styles import (
    HEADER_STYLE, NO_DATA_STYLE,
    FILTER_TAG_STYLE, PLATFORM_FILTER_STYLE, LANGUAGE_FILTER_STYLE,
    PLOTLY_TEMPLATE, LAYOUT_THEME
)

class GeographicDistributionTab:
    def __init__(self, data_manager, app):
        """Initialize the Geographic Distribution tab with a DataManager instance."""
        logger.info("Initializing Geographic Distribution tab")
        self.data_manager = data_manager
        self.app = app
        self.register_callbacks()
        logger.info("Geographic Distribution tab initialized successfully")

    def create_choropleth_map(self, df, filters_data=None):
        """Create choropleth map showing global session distribution."""
        logger.debug("Creating choropleth map")
        # Use provided filters or get from DataManager
        if filters_data is None:
            filters_data = self.data_manager.get_active_filters() or {}
        selected_country = filters_data.get('country')
        logger.debug(f"Selected country for map: {selected_country}")
        fig = go.Figure()
        
        if len(df) == 0:
            logger.debug("No data available for choropleth map")
            fig.update_layout(
                title="Global Session Distribution (No data available)",
                template=PLOTLY_TEMPLATE,
                **LAYOUT_THEME,
                showlegend=True
            )
            return fig
        
        country_data = df.groupby(['Country', 'CountryCode'])['Session'].nunique().reset_index()
        country_data = country_data.rename(columns={'Session': 'Sessions'})
       
        # Filter out any invalid country codes
        country_data = country_data.dropna(subset=['CountryCode'])

        # First add choropleth map for countries
        fig.add_trace(go.Choropleth(
            locations=country_data['CountryCode'],
            z=country_data['Sessions'],
            text=country_data['Country'],
            # colorscale=[
            #     [0, '#E8F5E9'],  # Light green for low values
            #     [0.5, '#66BB6A'],  # Medium green
            #     [1, '#1B5E20']  # Dark green for high values
            # ],
            autocolorscale=True,
            marker_line_color=country_data['Country'].apply(
                lambda x: '#1f77b4' if x == selected_country else 'darkgray'
            ),
            marker_line_width=country_data['Country'].apply(
                lambda x: 2 if x == selected_country else 0.5
            ),
            colorbar_title='Number of Sessions',
            customdata=country_data[['CountryCode']],
            hovertemplate="Country: <b>%{text}</b><br>Sessions: %{z:,}<br>ISO3166: %{customdata[0]}<extra></extra>"
        ))

        # Then add city markers on top
        city_data = df.groupby(['City', 'Country'])['Session'].nunique().reset_index()
        city_data = city_data.rename(columns={'Session': 'Sessions'})
        
        # Add city markers if we have any
        if len(city_data) > 0:
            # Filter out 'Unknown' cities
            city_data = city_data[city_data['City'] != 'Unknown']
            
            # Add coordinates from cities.csv
            city_coords = []
            for _, row in city_data.iterrows():
                coords = self.data_manager.get_city_coordinates(row['City'], row['Country'])
                if coords:
                    city_coords.append({
                        'City': row['City'],
                        'Country': row['Country'],
                        'Sessions': row['Sessions'],
                        'Longitude': coords[0],
                        'Latitude': coords[1]
                    })
            
            if city_coords:
                city_coords_df = pd.DataFrame(city_coords)
                
                # Calculate marker sizes with better scaling
                max_sessions = city_coords_df['Sessions'].max()
                min_size = 8
                max_size = 25
                city_coords_df['MarkerSize'] = city_coords_df['Sessions'].apply(
                    lambda x: min_size + (max_size - min_size) * (x / max_sessions)
                )
                
                fig.add_trace(go.Scattergeo(
                    lon=city_coords_df['Longitude'],
                    lat=city_coords_df['Latitude'],
                    text=city_coords_df.apply(lambda x: f"{x['City']}, {x['Country']}", axis=1),
                    mode='markers',
                    name='Cities',
                    marker=dict(
                        size=city_coords_df['MarkerSize'],
                        color='#E74C3C',  # Red color for visibility
                        line=dict(width=1, color='white'),
                        sizemode='diameter',
                        sizeref=1.0
                    ),
                    hovertemplate="<b>%{text}</b><br>Sessions: %{marker.size:,.0f}<extra></extra>"
                ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': "Global Session Distribution",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            template=PLOTLY_TEMPLATE,
            **LAYOUT_THEME,
            geo=dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor='lightgray',
                showland=True,
                landcolor='rgb(250, 250, 250)',
                showocean=True,
                oceancolor='rgb(245, 250, 255)',
                projection_type='natural earth',
                projection_scale=1,
                center=dict(lon=0, lat=0),  # Center the map slightly north
                showlakes=True,
                lakecolor='rgb(245, 250, 255)',
                showcountries=True,
                countrycolor='lightgray',
                countrywidth=0.5,
                showsubunits=True,
                subunitcolor='lightgray',
                subunitwidth=0.5
            ),
            height=600,  # Make the map taller
            margin=dict(l=0, r=0, t=50, b=0)  # Reduce margins
        )
        
        return fig

    def create_language_chart(self, df, selected_language=None):
        """Create language distribution chart."""
        logger.debug(f"Creating language chart with selected language: {selected_language}")
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
        logger.debug(f"Creating continent chart with selected continent: {selected_continent}")
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
        logger.debug(f"Creating country chart with continent: {selected_continent}, country: {selected_country}")
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
        logger.debug(f"Creating city chart with continent: {selected_continent}, country: {selected_country}")
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
        logger.info("Creating Geographic Distribution tab layout")
        active_filters = self.data_manager.get_active_filters()
        return [
                # Geographic Distribution Section
                html.Div([
                    html.H2("Geographic Distribution", style=HEADER_STYLE),
                    
                    # Bubble Map
                    html.Div([
                        dcc.Graph(
                            id='geo_choropleth_map',
                            figure=self.create_choropleth_map(initial_df, active_filters)
                        )
                    ]),
                    
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
        logger.info("Registering Geographic Distribution tab callbacks")
        @self.app.callback(
            [
                Output('geo_choropleth_map', 'figure'),
                Output('geo_continent', 'figure'),
                Output('geo_country', 'figure'),
                Output('geo_city', 'figure'),
                Output('geo_language', 'figure')
            ],
            [
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date'),
                Input('active-filters-store', 'data')
            ]
        )
        def update_charts(start_date, end_date, filters_data):
            """Update all charts based on date range and active filters."""
            logger.debug(f"Updating geographic charts for date range: {start_date} to {end_date}")
            try:
                # Get filtered data using the active filters from the store
                filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
                logger.info(f"Retrieved filtered dataset with {len(filtered_df)} records")
                
                # Update all charts with filters from the store
                return [
                    self.create_choropleth_map(filtered_df, filters_data),
                    self.create_continent_chart(filtered_df, selected_continent=filters_data.get('continent')),
                    self.create_country_chart(filtered_df, 
                                            selected_continent=filters_data.get('continent'),
                                            selected_country=filters_data.get('country')),
                    self.create_city_chart(filtered_df,
                                         selected_continent=filters_data.get('continent'),
                                         selected_country=filters_data.get('country')),
                    self.create_language_chart(filtered_df, selected_language=filters_data.get('language'))
                ]
            except Exception as e:
                logger.error(f"Error updating geographic charts: {str(e)}")
                raise
        
        @self.app.callback(
            Output('active-filters', 'children'),
            [Input('active-filters-store', 'data')]
        )
        def update_active_filters_display(active_filters):
            """Update the active filters display."""
            logger.debug("Updating active filters display")
            try:
                if active_filters is None:
                    active_filters = {}
                logger.debug(f"Active filters from store: {active_filters}")
                
                if not active_filters or len(active_filters) == 0:
                    logger.debug("No active filters")
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
            except Exception as e:
                logger.error(f"Error updating active filters display: {str(e)}")
                raise
