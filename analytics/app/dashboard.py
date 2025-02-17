import dash
from dash import html, dcc
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

def get_session_data():
    """Get session data from analytics database."""
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    query = "SELECT * FROM tblSessions ORDER BY timestamp"
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df

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

# Get the data
df = get_session_data()

# Create layout
app.layout = html.Div([
    html.H1("AI Anime Maker Analytics Dashboard", style={'textAlign': 'center'}),
    
    # Platform Statistics Section
    html.Div([
        html.H2("Platform Statistics", style={'textAlign': 'center'}),
        html.Div([
            html.Div([
                dcc.Graph(figure=create_os_chart(df))
            ], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Graph(figure=create_browser_chart(df))
            ], style={'width': '50%', 'display': 'inline-block'})
        ]),
        html.Div([
            dcc.Graph(figure=create_mobile_pie(df))
        ], style={'width': '50%', 'margin': '0 auto'})
    ]),
    
    # Geographic Distribution Section
    html.Div([
        html.H2("Geographic Distribution", style={'textAlign': 'center'}),
        html.Div([
            html.Div([
                dcc.Graph(figure=create_continent_chart(df))
            ], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([
                dcc.Graph(figure=create_country_chart(df))
            ], style={'width': '50%', 'display': 'inline-block'})
        ]),
        html.Div([
            dcc.Graph(figure=create_city_chart(df))
        ])
    ]),
    
    # Language Distribution Section
    html.Div([
        html.H2("Language Distribution", style={'textAlign': 'center'}),
        dcc.Graph(figure=create_language_chart(df))
    ])
])

# Get server for external use
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
