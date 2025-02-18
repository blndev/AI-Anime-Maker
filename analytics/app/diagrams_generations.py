import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Import shared theme settings and data access
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME
from .data import get_style_usage

def create_style_usage_chart(df, start_date=None, end_date=None):
    """Create pie chart showing generation style distribution with percentages."""
    # Get style usage data with percentages
    style_data = get_style_usage(df, start_date, end_date)
    
    # Create figure
    fig = go.Figure()
    
    # Add pie chart
    fig.add_trace(go.Pie(
        labels=style_data['Style'],
        values=style_data['Percentage'],
        marker=dict(colors=px.colors.qualitative.Set3),  # Use a color set that works well for pie charts
        textinfo='label+percent',  # Show both style name and percentage
        hovertemplate="<br>".join([
            "Style: %{label}",
            "Percentage: %{value:.1f}%",
            "Count: %{customdata[0]}",
            "<extra></extra>"
        ]),
        customdata=style_data[['Count']].values
    ))
    
    # Update layout
    fig.update_layout(
        title='Generation Style Distribution',
        template=PLOTLY_TEMPLATE,
        **LAYOUT_THEME,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig
