import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# Import shared theme settings and data access
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME
from .data import get_top_images

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
