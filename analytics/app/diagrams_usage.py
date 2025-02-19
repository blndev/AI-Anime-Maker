import plotly.express as px
import pandas as pd

# Import shared theme settings
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME

def create_os_chart(df, selected_os=None):
    """Create operating system distribution chart."""
    fig = px.bar(
        pd.DataFrame({'OS': [], 'Count': []}),
        x='OS',
        y='Count',
        title="Operating System Distribution",
        labels={'OS': 'Operating System', 'Count': 'Number of Sessions'},
        template=PLOTLY_TEMPLATE
    )
    
    if len(df) == 0:
        fig.update_layout(
            title="Operating System Distribution (No data available)",
            **LAYOUT_THEME,
            showlegend=False
        )
        return fig
    
    os_counts = df['OS'].value_counts().reset_index()
    os_counts.columns = ['OS', 'Count']
    
    fig = px.bar(
        os_counts,
        x='OS',
        y='Count',
        title="Operating System Distribution",
        labels={'OS': 'Operating System', 'Count': 'Number of Sessions'},
        template=PLOTLY_TEMPLATE
    )
    fig.update_layout(
        **LAYOUT_THEME,
        clickmode='event',
        dragmode='select'
    )
    
    # Highlight selected OS if any
    if selected_os:
        fig.update_traces(
            marker_color=[
                '#1f77b4' if x == selected_os else '#7fdbff' 
                for x in os_counts['OS']
            ]
        )
    return fig

def create_browser_chart(df, selected_browser=None):
    """Create browser distribution chart."""
    fig = px.bar(
        pd.DataFrame({'Browser': [], 'Count': []}),
        x='Browser',
        y='Count',
        title="Browser Distribution",
        labels={'Browser': 'Browser', 'Count': 'Number of Sessions'},
        template=PLOTLY_TEMPLATE
    )
    
    if len(df) == 0:
        fig.update_layout(
            title="Browser Distribution (No data available)",
            **LAYOUT_THEME,
            showlegend=False
        )
        return fig
    
    browser_counts = df['Browser'].value_counts().reset_index()
    browser_counts.columns = ['Browser', 'Count']
    
    fig = px.bar(
        browser_counts,
        x='Browser',
        y='Count',
        title="Browser Distribution",
        labels={'Browser': 'Browser', 'Count': 'Number of Sessions'},
        template=PLOTLY_TEMPLATE
    )
    fig.update_layout(
        **LAYOUT_THEME,
        clickmode='event',
        dragmode='select'
    )
    
    # Highlight selected browser if any
    if selected_browser:
        fig.update_traces(
            marker_color=[
                '#1f77b4' if x == selected_browser else '#7fdbff' 
                for x in browser_counts['Browser']
            ]
        )
    return fig
