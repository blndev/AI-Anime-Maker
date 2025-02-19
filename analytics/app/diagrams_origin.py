import plotly.express as px
import pandas as pd

# Import shared theme settings
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME

def create_language_chart(df, selected_language=None):
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

def create_continent_chart(df, selected_continent=None):
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

def create_country_chart(df, selected_continent=None, selected_country=None):
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

def create_city_chart(df, selected_continent=None, selected_country=None):
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
