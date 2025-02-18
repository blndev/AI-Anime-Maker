import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# Import shared theme settings and data access
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME
from .data import get_top_images

def create_image_uploads_timeline(df):
    """Create timeline of image uploads and generations aggregated by hour with local timezone."""
    # Create a copy of the dataframe
    data = df.copy()
    
    # Get timezone info from the timestamp column
    tz = data['Timestamp'].dt.tz
    tz_name = str(tz) if tz else 'Local'
    
    # Group by hour and aggregate metrics
    data['Hour'] = data['Timestamp'].dt.floor('H')
    hourly_data = data.groupby('Hour').agg({
        'ImageUploads': 'sum',
        'GenerationCount': 'sum',
        'Session': 'nunique'  # Count unique sessions
    }).reset_index()
    hourly_data = hourly_data.rename(columns={'Session': 'SessionCount'})
    
    # Create figure
    fig = go.Figure()
    
    # Add uploads bars
    fig.add_trace(
        go.Bar(
            x=hourly_data['Hour'],
            y=hourly_data['ImageUploads'],
            name='Uploads',
            marker_color='#4B89DC',
            hovertemplate="<br>".join([
                "Time: %{x}",
                "Total Uploads: %{y}",
                "<extra></extra>"
            ])
        )
    )
    
    # Add generations line
    fig.add_trace(
        go.Scatter(
            x=hourly_data['Hour'],
            y=hourly_data['GenerationCount'],
            name='Generations',
            line=dict(color='#E74C3C', width=2),
            hovertemplate="<br>".join([
                "Time: %{x}",
                "Total Generations: %{y}",
                "<extra></extra>"
            ])
        )
    )
    
    # Add sessions line
    fig.add_trace(
        go.Scatter(
            x=hourly_data['Hour'],
            y=hourly_data['SessionCount'],
            name='New Sessions',
            line=dict(color='#2ECC71', width=2, dash='dot'),
            hovertemplate="<br>".join([
                "Time: %{x}",
                "New Sessions: %{y}",
                "<extra></extra>"
            ])
        )
    )
    
    # Update layout
    fig.update_layout(
        title=f'Activity per Hour ({tz_name})',
        xaxis_title=f'Date & Time ({tz_name})',
        yaxis_title='Count',
        template=PLOTLY_TEMPLATE,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'  # Show all values for the same x coordinate
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
