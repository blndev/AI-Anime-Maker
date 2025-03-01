from dash import html, dcc, Input, Output, State
import dash
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

# Set up logging
logger = logging.getLogger(__name__)
from ..styles import HEADER_STYLE, FILTER_CONTAINER_STYLE, PLOTLY_TEMPLATE, LAYOUT_THEME

class UsageStatisticsTab:
    def __init__(self, data_manager, app):
        """Initialize the Usage Statistics tab with a DataManager instance."""
        logger.info("Initializing Usage Statistics tab")
        self.data_manager = data_manager
        self.app = app
        self.register_callbacks()
        logger.info("Usage Statistics tab initialized successfully")

    def create_sessions_timeline(self, df):
        """Create timeline of sessions."""
        logger.debug("Creating sessions timeline chart")
        # Create figure
        fig = go.Figure()
        
        if len(df) == 0:
            logger.debug("No session data available")
            fig.update_layout(
                title="Sessions Over Time (No data available)",
                xaxis_title="Date",
                yaxis_title="Number of Sessions",
                template=PLOTLY_TEMPLATE,
                **LAYOUT_THEME,
                showlegend=False
            )
            return fig
        
        try:
            # Convert and extract date from Timestamp
            df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
            
            # Create a complete date range
            date_range = pd.date_range(
                start=min(df['Date']),
                end=max(df['Date']),
                freq='D'
            )
            logger.debug(f"Created date range from {min(df['Date'])} to {max(df['Date'])}")
            
            # Create a DataFrame with all dates
            all_dates = pd.DataFrame({'Date': date_range.date})
            
            # Count sessions per date
            daily_counts = df.groupby('Date').size().reset_index(name='Count')
            
            # Merge with all dates to include zeros for missing dates
            daily_counts = pd.merge(
                all_dates,
                daily_counts,
                on='Date',
                how='left'
            ).fillna(0)
            
            # Convert Count to integer
            daily_counts['Count'] = daily_counts['Count'].astype(int)
            
            # Convert date objects to datetime for plotting
            daily_counts['Date'] = pd.to_datetime(daily_counts['Date'])
            
            # Sort by date
            daily_counts = daily_counts.sort_values('Date')
            
            # Create combined line and bar chart
            fig = go.Figure()
            
            # Add bar chart
            fig.add_trace(go.Bar(
                x=daily_counts['Date'],
                y=daily_counts['Count'],
                name='Daily Sessions',
                marker_color='#4B89DC'
            ))
            
            # Add line chart
            fig.add_trace(go.Scatter(
                x=daily_counts['Date'],
                y=daily_counts['Count'],
                name='Trend',
                line=dict(color='#A0D468'),
                mode='lines'
            ))
            
            # Update layout
            fig.update_layout(
                title="Sessions Over Time",
                xaxis_title="Date",
                yaxis_title="Number of Sessions",
                barmode='overlay',
                bargap=0.1,
                template=PLOTLY_TEMPLATE
            )
            fig.update_layout(**LAYOUT_THEME)
            
            return fig
        except Exception as e:
            logger.error(f"Error creating sessions timeline: {str(e)}")
            raise
        

    def create_mobile_pie(self, df):
        """Create mobile vs desktop pie chart."""
        logger.debug("Creating mobile vs desktop usage pie chart")
        try:
            fig = px.pie(
                pd.DataFrame({'Type': [], 'Count': []}),
                values='Count',
                names='Type',
                title="Desktop vs Mobile Usage",
                template=PLOTLY_TEMPLATE
            )
            
            if len(df) == 0:
                fig.update_layout(
                    title="Desktop vs Mobile Usage (No data available)",
                    **LAYOUT_THEME,
                    showlegend=False
                )
                return fig
            
            mobile_counts = df['IsMobile'].value_counts().reset_index()
            mobile_counts.columns = ['Type', 'Count']
            mobile_counts['Type'] = mobile_counts['Type'].map({0: 'Desktop', 1: 'Mobile'})
            
            fig = px.pie(
                mobile_counts,
                values='Count',
                names='Type',
                title="Desktop vs Mobile Usage",
                template=PLOTLY_TEMPLATE
            )
            fig.update_layout(**LAYOUT_THEME)
            return fig
        except Exception as e:
            logger.error(f"Error creating mobile pie chart: {str(e)}")
            raise

    def create_country_generation_rates(self, df):
        """Create time series chart showing sessions without generations by country (top 10)."""
        logger.debug("Creating country sessions without generations chart")
        try:
            fig = go.Figure()
            
            if len(df) == 0:
                fig.update_layout(
                    title="Sessions Without Generations by Country (No data available)",
                    xaxis_title="Date",
                    yaxis_title="Number of Sessions Without Generations",
                    template=PLOTLY_TEMPLATE,
                    **LAYOUT_THEME,
                    showlegend=False
                )
                return fig
            
            # Convert timestamp to date
            df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
            
            # Group by date and country, count sessions without generations
            country_metrics = df.groupby(['Date', 'Country']).agg({
                'HasStartedGeneration': lambda x: sum(x == 0)  # Count sessions where HasStartedGeneration is 0
            }).reset_index()
            
            # Rename column for clarity
            country_metrics.rename(columns={'HasStartedGeneration': 'SessionsWithoutGen'}, inplace=True)
            
            # Get top 10 countries by total sessions without generations
            top_countries = df[df['HasStartedGeneration'] == 0].groupby('Country').size().nlargest(10).index
            
            # Create a line for each top country
            for country in top_countries:
                country_data = country_metrics[country_metrics['Country'] == country]
                if not country_data.empty:
                    fig.add_trace(go.Scatter(
                        x=country_data['Date'],
                        y=country_data['SessionsWithoutGen'],
                        name=country,
                        mode='lines+markers',
                    ))
            
            fig.update_layout(
                title="Sessions Without Generations by Country (Top 10)",
                xaxis_title="Date",
                yaxis_title="Number of Sessions Without Generations",
                template=PLOTLY_TEMPLATE,
                **LAYOUT_THEME
            )
            
            return fig
        except Exception as e:
            logger.error(f"Error creating country generation rates chart: {str(e)}")
            raise

    def create_generation_status_chart(self, df):
        """Create pie chart showing ratio of users who started/didn't start generations."""
        logger.debug("Creating generation status pie chart")
        try:
            fig = px.pie(
                pd.DataFrame({'Status': [], 'Count': []}),
                values='Count',
                names='Status',
                title="Users Who Started Generations",
                template=PLOTLY_TEMPLATE
            )
            
            if len(df) == 0:
                fig.update_layout(
                    title="Users Who Started Generations (No data available)",
                    **LAYOUT_THEME,
                    showlegend=False
                )
                return fig
            
            status_counts = df['HasStartedGeneration'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            status_counts['Status'] = status_counts['Status'].map({
                1: 'Started Generation',
                0: 'No Generation Started'
            })
            
            fig = px.pie(
                status_counts,
                values='Count',
                names='Status',
                title="Users Who Started Generations",
                template=PLOTLY_TEMPLATE
            )
            fig.update_layout(**LAYOUT_THEME)
            return fig
        except Exception as e:
            logger.error(f"Error creating generation status chart: {str(e)}")
            raise

    def create_os_chart(self, df, selected_os=None):
        """Create operating system distribution chart."""
        logger.debug(f"Creating OS distribution chart with selected OS: {selected_os}")
        try:
            fig = px.bar(
                pd.DataFrame({'OS': [], 'Count': []}),
                x='OS',
                y='Count',
                title="Operating System Distribution",
                labels={'OS': 'Operating System', 'Count': 'Number of Sessions'},
                template=PLOTLY_TEMPLATE
            )
            
            if len(df) == 0:
                fig.update_layout(
                    title="Operating System Distribution (No data available)",
                    **LAYOUT_THEME,
                    showlegend=False
                )
                return fig
            
            os_counts = df['OS'].value_counts().reset_index()
            os_counts.columns = ['OS', 'Count']
            
            fig = px.bar(
                os_counts,
                x='OS',
                y='Count',
                title="Operating System Distribution",
                labels={'OS': 'Operating System', 'Count': 'Number of Sessions'},
                template=PLOTLY_TEMPLATE
            )
            fig.update_layout(
                **LAYOUT_THEME,
                clickmode='event',
                dragmode='select'
            )
            
            # Highlight selected OS if any
            if selected_os:
                fig.update_traces(
                    marker_color=[
                        '#1f77b4' if x == selected_os else '#7fdbff' 
                        for x in os_counts['OS']
                    ]
                )
            return fig
        except Exception as e:
            logger.error(f"Error creating OS chart: {str(e)}")
            raise

    def create_browser_chart(self, df, selected_browser=None):
        """Create browser distribution chart."""
        logger.debug(f"Creating browser distribution chart with selected browser: {selected_browser}")
        try:
            fig = px.bar(
                pd.DataFrame({'Browser': [], 'Count': []}),
                x='Browser',
                y='Count',
                title="Browser Distribution",
                labels={'Browser': 'Browser', 'Count': 'Number of Sessions'},
                template=PLOTLY_TEMPLATE
            )
            
            if len(df) == 0:
                fig.update_layout(
                    title="Browser Distribution (No data available)",
                    **LAYOUT_THEME,
                    showlegend=False
                )
                return fig
            
            browser_counts = df['Browser'].value_counts().reset_index()
            browser_counts.columns = ['Browser', 'Count']
            
            fig = px.bar(
                browser_counts,
                x='Browser',
                y='Count',
                title="Browser Distribution",
                labels={'Browser': 'Browser', 'Count': 'Number of Sessions'},
                template=PLOTLY_TEMPLATE
            )
            fig.update_layout(
                **LAYOUT_THEME,
                clickmode='event',
                dragmode='select'
            )
            
            # Highlight selected browser if any
            if selected_browser:
                fig.update_traces(
                    marker_color=[
                        '#1f77b4' if x == selected_browser else '#7fdbff' 
                        for x in browser_counts['Browser']
                    ]
                )
            return fig
        except Exception as e:
            logger.error(f"Error creating browser chart: {str(e)}")
            raise
        
    def create_layout(self, initial_df):
        """Create the layout for the Usage Statistics tab."""
        logger.info("Creating Usage Statistics tab layout")
        # Get initial filter options
        filter_options = self.data_manager.get_filter_options()
        
        return [
            # Sessions Timeline
            html.Div([
                dcc.Graph(id='usage_timeline', figure=self.create_sessions_timeline(initial_df))
            ]),
            
            # Platform Statistics Section
            html.Div([
                html.H2("Platform Statistics", style=HEADER_STYLE),
                
                # OS and Browser Charts
                html.Div([
                    html.Div([
                        dcc.Graph(id='usage_os', figure=self.create_os_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='usage_browser', figure=self.create_browser_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'})
                ]),
                
                # Mobile and Generation Status Charts
                html.Div([
                    html.Div([
                        dcc.Graph(id='usage_mobile', figure=self.create_mobile_pie(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='usage_generations', figure=self.create_generation_status_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'})
                ])
            ]),

            # Country Generation Rates
            html.Div([
                dcc.Graph(id='usage_country_rates', figure=self.create_country_generation_rates(initial_df))
            ])
        ]
    
    def register_callbacks(self):
        """Register callbacks for the Usage Statistics tab."""
        logger.info("Registering Usage Statistics tab callbacks")
        @self.app.callback(
            [
                Output('usage_timeline', 'figure'),
                Output('usage_os', 'figure'),
                Output('usage_browser', 'figure'),
                Output('usage_mobile', 'figure'),
                Output('usage_generations', 'figure'),
                Output('usage_country_rates', 'figure')
            ],
            [
                Input('active-filters-store', 'data'),
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date'),
                Input('usage_os', 'clickData'),
                Input('usage_browser', 'clickData')
            ]
        )
        def update_usage_charts(filters_data, start_date, end_date, os_click, browser_click):
            """Update all usage statistics charts."""
            logger.debug(f"Updating usage charts for date range: {start_date} to {end_date}")
            try:
                # Get filtered data using the filters from the store
                if filters_data is None:
                    filters_data = {}
                
                filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
                logger.info(f"Retrieved filtered dataset with {len(filtered_df)} records")
                
                return [
                    self.create_sessions_timeline(filtered_df),
                    self.create_os_chart(filtered_df, filters_data.get('os')),
                    self.create_browser_chart(filtered_df, filters_data.get('browser')),
                    self.create_mobile_pie(filtered_df),
                    self.create_generation_status_chart(filtered_df),
                    self.create_country_generation_rates(filtered_df)
                ]
            except Exception as e:
                logger.error(f"Error updating usage charts: {str(e)}")
                raise
