import plotly.express as px
import pandas as pd

# Import shared theme settings
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME

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
