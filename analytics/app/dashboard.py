import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

# Initialize the Dash app
app = dash.Dash(__name__, title="AI Anime Maker Analytics")

def get_session_data(start_date=None, end_date=None):
    """Get session data from analytics database.
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
    """
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    query = "SELECT *, date(Timestamp) as Date FROM tblSessions"
    params = []
    
    if start_date and end_date:
        query += " WHERE date(Timestamp) BETWEEN ? AND ?"
        params = [start_date, end_date]
    
    query += " ORDER BY Timestamp"
    
    df = pd.read_sql_query(query, connection, params=params)
    connection.close()
    return df

def create_sessions_timeline(df):
    """Create timeline of sessions."""
    daily_counts = df.groupby('Date').size().reset_index()
    daily_counts.columns = ['Date', 'Count']
    
    fig = px.line(
        daily_counts,
        x='Date',
        y='Count',
        title="Sessions Over Time",
        labels={'Date': 'Date', 'Count': 'Number of Sessions'}
    )
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
        labels={'OS': 'Operating System', 'Count': 'Number of Sessions'}
    )
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
        labels={'Browser': 'Browser', 'Count': 'Number of Sessions'}
    )
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
        title="Desktop vs Mobile Usage"
    )
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
        labels={'Continent': 'Continent', 'Count': 'Number of Sessions'}
    )
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
        labels={'Country': 'Country', 'Count': 'Number of Sessions'}
    )
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
        labels={'Language': 'Language', 'Count': 'Number of Sessions'}
    )
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
        labels={'City': 'City', 'Count': 'Number of Sessions'}
    )
    return fig

# Initialize with last 30 days of data
initial_end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
initial_start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')

# Get initial data
df = get_session_data(initial_start_date, initial_end_date)

# Create layout
app.layout = html.Div([
    html.H1("AI Anime Maker Analytics Dashboard", style={'textAlign': 'center'}),
    
    # Date Range Selector
    html.Div([
        html.H2("Date Range Selection", style={'textAlign': 'center'}),
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
    
    # Sessions Timeline
    html.Div([
        dcc.Graph(id='timeline-chart', figure=create_sessions_timeline(df))
    ]),
    
    # Platform Statistics Section
    html.Div([
        html.H2("Platform Statistics", style={'textAlign': 'center'}),
        html.Div([
            html.Div([
                dcc.Graph(id='os-chart', figure=create_os_chart(df))
            ], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Graph(id='browser-chart', figure=create_browser_chart(df))
            ], style={'width': '50%', 'display': 'inline-block'})
        ]),
        html.Div([
            dcc.Graph(id='mobile-chart', figure=create_mobile_pie(df))
        ], style={'width': '50%', 'margin': '0 auto'})
    ]),
    
    # Geographic Distribution Section
    html.Div([
        html.H2("Geographic Distribution", style={'textAlign': 'center'}),
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
    ]),
    
    # Language Distribution Section
    html.Div([
        html.H2("Language Distribution", style={'textAlign': 'center'}),
        dcc.Graph(id='language-chart', figure=create_language_chart(df))
    ])
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
        Output('language-chart', 'figure')
    ],
    [
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_charts(start_date, end_date):
    """Update all charts based on selected date range."""
    df = get_session_data(start_date, end_date)
    return [
        create_sessions_timeline(df),
        create_os_chart(df),
        create_browser_chart(df),
        create_mobile_pie(df),
        create_continent_chart(df),
        create_country_chart(df),
        create_city_chart(df),
        create_language_chart(df)
    ]

# Get server for external use
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
