import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys

# Import shared theme settings
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import src.config as config

def get_top_images():
    """Get top 10 most frequently uploaded images with their paths."""
    config.read_configuration()
    connection = sqlite3.connect(config.get_analytics_db_path())
    
    query = """
    SELECT 
        SHA1,
        CachePath,
        COUNT(*) as UploadCount
    FROM tblInput
    GROUP BY SHA1, CachePath
    ORDER BY UploadCount DESC
    LIMIT 10
    """
    
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df

def create_image_uploads_timeline(df):
    """Create timeline of image uploads per session."""
    # Only include sessions with uploads
    upload_data = df[df['ImageUploads'] > 0].copy()
    
    # Create timeline
    fig = px.scatter(
        upload_data,
        x='Timestamp',
        y='ImageUploads',
        title='Image Uploads per Session Over Time',
        labels={
            'Timestamp': 'Date',
            'ImageUploads': 'Number of Uploads'
        },
        template=PLOTLY_TEMPLATE
    )
    
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_top_images_chart(df):
    """Create bar chart of top uploaded images with thumbnails."""
    # Create figure with subplots: bar chart on top, image grid below
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=df['SHA1'],
        y=df['UploadCount'],
        name='Upload Count',
        marker_color='#4B89DC'
    ))
    
    # Add hover text with image paths
    fig.update_traces(
        hovertemplate="<br>".join([
            "Image Hash: %{x}",
            "Upload Count: %{y}",
            "Path: %{customdata}"
        ]),
        customdata=df['CachePath']
    )
    
    # Update layout
    fig.update_layout(
        title='Top 10 Most Frequently Uploaded Images',
        xaxis_title='Image Hash',
        yaxis_title='Number of Uploads',
        template=PLOTLY_TEMPLATE,
        **LAYOUT_THEME
    )
    
    return fig
