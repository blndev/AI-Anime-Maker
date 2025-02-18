import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys
import logging

# Define dark theme settings
PLOTLY_TEMPLATE = 'plotly_dark'
LAYOUT_THEME = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)'
}

# Define layout styles
LAYOUT_STYLE = {
    'backgroundColor': '#111111',
    'color': '#FFFFFF',
    'minHeight': '100vh',
    'padding': '20px'
}

HEADER_STYLE = {
    'textAlign': 'center',
    'color': '#FFFFFF'
}

# Define tab styles
TAB_STYLE = {
    'backgroundColor': '#1e1e1e',
    'color': '#cccccc',
    'padding': '10px',
    'border': '1px solid #333333'
}

TAB_SELECTED_STYLE = {
    'backgroundColor': '#2d2d2d',
    'color': '#ffffff',
    'padding': '10px',
    'border': '1px solid #444444'
}

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with formatting
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(console_handler)

# Initialize the Dash app
app = dash.Dash(__name__, title="AI Anime Maker Analytics")

def get_session_data(start_date=None, end_date=None, include_generation_status=False):
    """Get session data from analytics database.
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    """
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    # Handle datetime format YYYY-MM-DD HH:MM:SS
    if include_generation_status:
        query = """
        SELECT 
            s.*,
            date(s.Timestamp) as Date,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM tblGenerations g WHERE g.Session = s.Session
                    UNION
                    SELECT 1 FROM tblInput i WHERE i.Session = s.Session
                ) THEN 1
                ELSE 0
            END as HasStartedGeneration
        FROM tblSessions s
        """
        if start_date and end_date:
            query += " WHERE date(s.Timestamp) BETWEEN ? AND ?"
        query += " ORDER BY s.Timestamp"
    else:
        query = "SELECT *, date(Timestamp) as Date FROM tblSessions"
        if start_date and end_date:
            query += " WHERE date(Timestamp) BETWEEN ? AND ?"
        query += " ORDER BY Timestamp"
    
    params = [start_date, end_date] if start_date and end_date else []
    
    df = pd.read_sql_query(query, connection, params=params)
    connection.close()
    
    # Log data loading info
    logger.info(f"Data loaded: {len(df)} rows")
    if len(df) > 0:
        logger.debug(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        logger.debug(f"Sample dates: {df['Date'].head().tolist()}")
    
    return df

def create_sessions_timeline(df):
    """Create timeline of sessions."""
    # Log timeline debug info
    logger.debug("Timeline processing started")
    logger.debug(f"DataFrame shape: {df.shape}")
    logger.debug(f"Columns: {df.columns.tolist()}")
    logger.debug(f"Sample Timestamps: {df['Timestamp'].head().tolist()}")
    
    # Convert and extract date from Timestamp
    df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
    
    # Create a complete date range
    if len(df) > 0:
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
        
        logger.debug("Daily counts after filling gaps:")
        logger.debug(f"Shape: {daily_counts.shape}")
        logger.debug(f"Date range: {daily_counts['Date'].min()} to {daily_counts['Date'].max()}")
        logger.debug(f"Sample counts:\n{daily_counts.head()}")
        
        # Convert date objects to datetime for plotting
        daily_counts['Date'] = pd.to_datetime(daily_counts['Date'])
        
        # Sort by date
        daily_counts = daily_counts.sort_values('Date')
    else:
        # Create empty DataFrame if no data
        daily_counts = pd.DataFrame(columns=['Date', 'Count'])
    
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

def create_os_chart(df):
    """Create operating system distribution chart."""
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
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_browser_chart(df):
    """Create browser distribution chart."""
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
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_mobile_pie(df):
    """Create mobile vs desktop pie chart."""
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

def create_continent_chart(df):
    """Create continent distribution chart."""
    continent_counts = df['Continent'].fillna('Unknown').value_counts().reset_index()
    continent_counts.columns = ['Continent', 'Count']
    fig = px.bar(
        continent_counts,
        x='Continent',
        y='Count',
        title="Geographic Distribution by Continent",
        labels={'Continent': 'Continent', 'Count': 'Number of Sessions'},
        template=PLOTLY_TEMPLATE
    )
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_country_chart(df):
    """Create country distribution chart."""
    country_counts = df['Country'].fillna('Unknown').value_counts().head(10).reset_index()
    country_counts.columns = ['Country', 'Count']
    fig = px.bar(
        country_counts,
        x='Country',
        y='Count',
        title="Top 10 Countries by Usage",
        labels={'Country': 'Country', 'Count': 'Number of Sessions'},
        template=PLOTLY_TEMPLATE
    )
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_language_chart(df):
    """Create language distribution chart."""
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
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_city_chart(df):
    """Create city distribution chart."""
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

def create_generation_status_chart(df):
    """Create pie chart showing ratio of users who started/didn't start generations."""
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

# Initialize with last 30 days of data
initial_end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
initial_start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')

# Get initial data
df = get_session_data(initial_start_date, initial_end_date, include_generation_status=True)

# Create layout
app.layout = html.Div(style=LAYOUT_STYLE, children=[
    html.H1("AI Anime Maker Analytics Dashboard", style=HEADER_STYLE),
    
    # Date Range Selector
    html.Div([
        html.H2("Date Range Selection", style=HEADER_STYLE),
        html.Div([
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed='2024-01-01',  # Adjust as needed
                max_date_allowed=initial_end_date,
                start_date=initial_start_date,
                end_date=initial_end_date,
                display_format='YYYY-MM-DD'
            )
        ], style={'textAlign': 'center', 'margin': '20px'}),
    ]),
    
    # Tabs
    dcc.Tabs([
        # Tab 1: Usage Statistics
        dcc.Tab(
            label='Usage Statistics',
            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE,
            children=[
                # Sessions Timeline
                html.Div([
                    dcc.Graph(id='timeline-chart', figure=create_sessions_timeline(df))
                ]),
                
                # Platform Statistics Section
                html.Div([
                    html.H2("Platform Statistics", style=HEADER_STYLE),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='os-chart', figure=create_os_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            dcc.Graph(id='browser-chart', figure=create_browser_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='mobile-chart', figure=create_mobile_pie(df))
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            dcc.Graph(id='generation-status-chart', figure=create_generation_status_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ])
                ])
            ]
        ),
        
        # Tab 2: Language and Geographic Distribution
        dcc.Tab(
            label='Language & Geographic Distribution',
            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE,
            children=[
                # Language Distribution Section
                html.Div([
                    html.H2("Language Distribution", style=HEADER_STYLE),
                    dcc.Graph(id='language-chart', figure=create_language_chart(df))
                ]),
                
                # Geographic Distribution Section
                html.Div([
                    html.H2("Geographic Distribution", style=HEADER_STYLE),
                    html.Div([
                        html.Div([
                            dcc.Graph(id='continent-chart', figure=create_continent_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            dcc.Graph(id='country-chart', figure=create_country_chart(df))
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    html.Div([
                        dcc.Graph(id='city-chart', figure=create_city_chart(df))
                    ])
                ])
            ]
        )
    ], style={'margin': '20px 0'})
])

# Callback to update all charts when date range changes
@app.callback(
    [
        Output('timeline-chart', 'figure'),
        Output('os-chart', 'figure'),
        Output('browser-chart', 'figure'),
        Output('mobile-chart', 'figure'),
        Output('continent-chart', 'figure'),
        Output('country-chart', 'figure'),
        Output('city-chart', 'figure'),
        Output('language-chart', 'figure'),
        Output('generation-status-chart', 'figure')
    ],
    [
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_charts(start_date, end_date):
    """Update all charts based on selected date range."""
    df = get_session_data(start_date, end_date, include_generation_status=True)
    return [
        create_sessions_timeline(df),
        create_os_chart(df),
        create_browser_chart(df),
        create_mobile_pie(df),
        create_continent_chart(df),
        create_country_chart(df),
        create_city_chart(df),
        create_language_chart(df),
        create_generation_status_chart(df)
    ]

# Get server for external use
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
