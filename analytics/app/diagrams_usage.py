import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Import shared theme settings
from .styles import PLOTLY_TEMPLATE, LAYOUT_THEME

def create_sessions_timeline(df):
    """Create timeline of sessions."""
    # Create figure
    fig = go.Figure()
    
    if len(df) == 0:
        fig.update_layout(
            title="Sessions Over Time (No data available)",
            xaxis_title="Date",
            yaxis_title="Number of Sessions",
            template=PLOTLY_TEMPLATE,
            **LAYOUT_THEME,
            showlegend=False
        )
        return fig
    
    # Convert and extract date from Timestamp
    df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
    
    # Create a complete date range
    date_range = pd.date_range(
        start=min(df['Date']),
        end=max(df['Date']),
        freq='D'
    )
    
    # Create a DataFrame with all dates
    all_dates = pd.DataFrame({'Date': date_range.date})
    
    # Count sessions per date
    daily_counts = df.groupby('Date').size().reset_index(name='Count')
    
    # Merge with all dates to include zeros for missing dates
    daily_counts = pd.merge(
        all_dates,
        daily_counts,
        on='Date',
        how='left'
    ).fillna(0)
    
    # Convert Count to integer
    daily_counts['Count'] = daily_counts['Count'].astype(int)
    
    # Convert date objects to datetime for plotting
    daily_counts['Date'] = pd.to_datetime(daily_counts['Date'])
    
    # Sort by date
    daily_counts = daily_counts.sort_values('Date')
    
    # Create combined line and bar chart
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=daily_counts['Date'],
        y=daily_counts['Count'],
        name='Daily Sessions',
        marker_color='#4B89DC'
    ))
    
    # Add line chart
    fig.add_trace(go.Scatter(
        x=daily_counts['Date'],
        y=daily_counts['Count'],
        name='Trend',
        line=dict(color='#A0D468'),
        mode='lines'
    ))
    
    # Update layout
    fig.update_layout(
        title="Sessions Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Sessions",
        barmode='overlay',
        bargap=0.1,
        template=PLOTLY_TEMPLATE
    )
    fig.update_layout(**LAYOUT_THEME)
    
    return fig

def create_os_chart(df):
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
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_browser_chart(df):
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
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_mobile_pie(df):
    """Create mobile vs desktop pie chart."""
    fig = px.pie(
        pd.DataFrame({'Type': [], 'Count': []}),
        values='Count',
        names='Type',
        title="Desktop vs Mobile Usage",
        template=PLOTLY_TEMPLATE
    )
    
    if len(df) == 0:
        fig.update_layout(
            title="Desktop vs Mobile Usage (No data available)",
            **LAYOUT_THEME,
            showlegend=False
        )
        return fig
    
    mobile_counts = df['IsMobile'].value_counts().reset_index()
    mobile_counts.columns = ['Type', 'Count']
    mobile_counts['Type'] = mobile_counts['Type'].map({0: 'Desktop', 1: 'Mobile'})
    
    fig = px.pie(
        mobile_counts,
        values='Count',
        names='Type',
        title="Desktop vs Mobile Usage",
        template=PLOTLY_TEMPLATE
    )
    fig.update_layout(**LAYOUT_THEME)
    return fig

def create_generation_status_chart(df):
    """Create pie chart showing ratio of users who started/didn't start generations."""
    fig = px.pie(
        pd.DataFrame({'Status': [], 'Count': []}),
        values='Count',
        names='Status',
        title="Users Who Started Generations",
        template=PLOTLY_TEMPLATE
    )
    
    if len(df) == 0:
        fig.update_layout(
            title="Users Who Started Generations (No data available)",
            **LAYOUT_THEME,
            showlegend=False
        )
        return fig
    
    status_counts = df['HasStartedGeneration'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    status_counts['Status'] = status_counts['Status'].map({
        1: 'Started Generation',
        0: 'No Generation Started'
    })
    
    fig = px.pie(
        status_counts,
        values='Count',
        names='Status',
        title="Users Who Started Generations",
        template=PLOTLY_TEMPLATE
    )
    fig.update_layout(**LAYOUT_THEME)
    return fig
