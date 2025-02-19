from dash import html, dcc, Input, Output, State
import dash
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from ..styles import HEADER_STYLE, FILTER_CONTAINER_STYLE, PLOTLY_TEMPLATE, LAYOUT_THEME
from ..diagrams_usage import create_os_chart, create_browser_chart

def create_sessions_timeline(df):
    """Create timeline of sessions."""
    # Create figure
    fig = go.Figure()
    
    if len(df) == 0:
        fig.update_layout(
            title="Sessions Over Time (No data available)",
            xaxis_title="Date",
            yaxis_title="Number of Sessions",
            template=PLOTLY_TEMPLATE,
            **LAYOUT_THEME,
            showlegend=False
        )
        return fig
    
    # Convert and extract date from Timestamp
    df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
    
    # Create a complete date range
    date_range = pd.date_range(
        start=min(df['Date']),
        end=max(df['Date']),
        freq='D'
    )
    
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

def create_mobile_pie(df):
    """Create mobile vs desktop pie chart."""
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

def create_generation_status_chart(df):
    """Create pie chart showing ratio of users who started/didn't start generations."""
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

class UsageStatisticsTab:
    def __init__(self, data_manager):
        """Initialize the Usage Statistics tab with a DataManager instance."""
        self.data_manager = data_manager
        
    def create_layout(self, initial_df):
        """Create the layout for the Usage Statistics tab."""
        # Get initial filter options
        filter_options = self.data_manager.get_filter_options()
        
        return [
            # Sessions Timeline
            html.Div([
                dcc.Graph(id='usage_timeline', figure=create_sessions_timeline(initial_df))
            ]),
            
            # Platform Statistics Section
            html.Div([
                html.H2("Platform Statistics", style=HEADER_STYLE),
                
                # OS and Browser Charts
                html.Div([
                    html.Div([
                        dcc.Graph(id='usage_os', figure=create_os_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='usage_browser', figure=create_browser_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'})
                ]),
                
                # Mobile and Generation Status Charts
                html.Div([
                    html.Div([
                        dcc.Graph(id='usage_mobile', figure=create_mobile_pie(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='usage_generations', figure=create_generation_status_chart(initial_df))
                    ], style={'width': '50%', 'display': 'inline-block'})
                ])
            ])
        ]
    
    def register_callbacks(self, app):
        """Register callbacks for the Usage Statistics tab."""
        @app.callback(
            [
                Output('usage_timeline', 'figure'),
                Output('usage_os', 'figure'),
                Output('usage_browser', 'figure'),
                Output('usage_mobile', 'figure'),
                Output('usage_generations', 'figure')
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
            # Initialize filters
            if filters_data is None:
                filters_data = {}
            
            # Handle OS click
            os_filter = None
            if os_click and 'points' in os_click and len(os_click['points']) > 0:
                os_filter = os_click['points'][0]['x']  # Get clicked OS name
                filters_data['os'] = os_filter
            
            # Handle Browser click
            browser_filter = None
            if browser_click and 'points' in browser_click and len(browser_click['points']) > 0:
                browser_filter = browser_click['points'][0]['x']  # Get clicked browser name
                filters_data['browser'] = browser_filter
            
            # Get filtered data
            filtered_df = self.data_manager.prepare_filtered_data(start_date, end_date, filters_data)
            
            return [
                create_sessions_timeline(filtered_df),
                create_os_chart(filtered_df, os_filter),
                create_browser_chart(filtered_df, browser_filter),
                create_mobile_pie(filtered_df),
                create_generation_status_chart(filtered_df)
            ]
