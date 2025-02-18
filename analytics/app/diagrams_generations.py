import plotly.graph_objects as go
import pandas as pd

# Import shared theme settings and data access
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME
from .data import get_style_usage

def create_style_usage_chart(df):
    """Create bar chart showing most used generation styles."""
    # Get style usage data
    style_data = get_style_usage(df)
    
    # Create figure
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=style_data['Style'],
        y=style_data['Count'],
        name='Usage Count',
        marker_color='#9B59B6'  # Purple to differentiate from other charts
    ))
    
    # Add hover text
    fig.update_traces(
        hovertemplate="<br>".join([
            "Style: %{x}",
            "Times Used: %{y}",
            "<extra></extra>"
        ])
    )
    
    # Update layout
    fig.update_layout(
        title='Most Used Generation Styles',
        xaxis_title='Style',
        yaxis_title='Number of Uses',
        template=PLOTLY_TEMPLATE,
        **LAYOUT_THEME
    )
    
    return fig
