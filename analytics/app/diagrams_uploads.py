import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# Import shared theme settings and data access
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME
from .data import get_top_images

def create_image_uploads_timeline(df):
    """Create timeline of image uploads aggregated by hour with local timezone."""
    # Only include sessions with uploads
    upload_data = df[df['ImageUploads'] > 0].copy()
    
    # Get timezone info from the timestamp column
    tz = upload_data['Timestamp'].dt.tz
    tz_name = str(tz) if tz else 'Local'
    
    # Group by hour and sum uploads
    upload_data['Hour'] = upload_data['Timestamp'].dt.floor('H')
    hourly_uploads = upload_data.groupby('Hour')['ImageUploads'].sum().reset_index()
    
    # Create timeline
    fig = px.bar(
        hourly_uploads,
        x='Hour',
        y='ImageUploads',
        title=f'Image Uploads per Hour ({tz_name})',
        labels={
            'Hour': f'Date & Time ({tz_name})',
            'ImageUploads': 'Number of Uploads'
        },
        template=PLOTLY_TEMPLATE
    )
    
    # Update hover template to show full datetime and upload count
    fig.update_traces(
        hovertemplate="<br>".join([
            "Time: %{x}",
            "Total Uploads: %{y}",
            "<extra></extra>"
        ])
    )
    
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_top_images_chart(df):
    """Create bar chart of top uploaded images with thumbnails."""
    # Create figure with subplots: bar chart on top, image grid below
    fig = go.Figure()
    
    # Extract image names from paths for x-axis labels
    df['ImageName'] = df['CachePath'].apply(lambda x: os.path.basename(x) if pd.notna(x) else 'Unknown')
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=df['ImageName'],
        y=df['UploadCount'],
        name='Upload Count',
        marker_color='#4B89DC'
    ))
    
    # Add hover text with image paths
    fig.update_traces(
        hovertemplate="<br>".join([
            "Image: %{x}",
            "Upload Count: %{y}",
            "Path: %{customdata}"
        ]),
        customdata=df['CachePath']
    )
    
    # Update layout
    fig.update_layout(
        title='Top 10 Most Frequently Uploaded Images',
        xaxis_title='Image Name',
        yaxis_title='Number of Uploads',
        template=PLOTLY_TEMPLATE,
        **LAYOUT_THEME
    )
    
    return fig
