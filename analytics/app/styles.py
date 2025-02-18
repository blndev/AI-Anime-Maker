"""
Theme and layout styles for the analytics dashboard.
"""

# Theme settings for plotly charts
PLOTLY_TEMPLATE = 'plotly_dark'
LAYOUT_THEME = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)'
}

# Layout styles
LAYOUT_STYLE = {
    'backgroundColor': '#111111',
    'color': '#FFFFFF',
    'minHeight': '100vh',
    'padding': '20px'
}

HEADER_STYLE = {
    'textAlign': 'center',
    'color': '#FFFFFF'
}

# Tab styles
TAB_STYLE = {
    'backgroundColor': '#1e1e1e',
    'color': '#cccccc',
    'padding': '10px',
    'border': '1px solid #333333'
}

TAB_SELECTED_STYLE = {
    'backgroundColor': '#2d2d2d',
    'color': '#ffffff',
    'padding': '10px',
    'border': '1px solid #444444'
}
