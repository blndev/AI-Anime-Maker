"""
Theme and layout styles for the analytics dashboard.
"""

# Color palette
COLORS = {
    # Primary colors
    'PRIMARY': '#4CAF50',  # Green
    'SECONDARY': '#2980B9', # Blue
    'ACCENT': '#8E44AD',   # Purple
    
    # Background colors
    'BG_DARK': '#111111',   # Main background
    'BG_MEDIUM': '#2C3E50', # Container background
    'BG_LIGHT': '#34495E',  # Light container background
    
    # Tab colors
    'TAB_BG': '#1e1e1e',
    'TAB_BG_SELECTED': '#2d2d2d',
    'TAB_BORDER': '#333333',
    'TAB_BORDER_SELECTED': '#444444',
    
    # Text colors
    'TEXT_PRIMARY': '#FFFFFF',
    'TEXT_SECONDARY': '#cccccc',
    'TEXT_MUTED': '#95A5A6',
    
    # Border colors
    'BORDER_DARK': '#333'
}

# Theme settings for plotly charts
PLOTLY_TEMPLATE = 'plotly_dark'
LAYOUT_THEME = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'hoverlabel': {
        'bgcolor': 'rgba(45, 45, 45, 0.9)',
        'font_size': 12,
        'font_color': COLORS['TEXT_PRIMARY']
    }
}

# Layout styles
LAYOUT_STYLE = {
    'backgroundColor': COLORS['BG_DARK'],
    'color': COLORS['TEXT_PRIMARY'],
    'minHeight': '100vh',
    'padding': '20px'
}

HEADER_STYLE = {
    'textAlign': 'center',
    'color': COLORS['TEXT_PRIMARY']
}

# Tab styles
TAB_STYLE = {
    'backgroundColor': COLORS['TAB_BG'],
    'color': COLORS['TEXT_SECONDARY'],
    'padding': '10px',
    'border': f"1px solid {COLORS['TAB_BORDER']}"
}

TAB_SELECTED_STYLE = {
    'backgroundColor': COLORS['TAB_BG_SELECTED'],
    'color': COLORS['TEXT_PRIMARY'],
    'padding': '10px',
    'border': f"1px solid {COLORS['TAB_BORDER_SELECTED']}"
}

# Filter styles
FILTER_CONTAINER_STYLE = {
    'display': 'flex',
    'justifyContent': 'space-between',
    'alignItems': 'center',
    'margin': '20px',
    'padding': '10px',
    'backgroundColor': COLORS['BG_MEDIUM'],
    'borderRadius': '4px'
}

FILTER_BUTTON_STYLE = {
    'backgroundColor': COLORS['PRIMARY'],
    'color': COLORS['TEXT_PRIMARY'],
    'padding': '10px 20px',
    'border': 'none',
    'borderRadius': '4px',
    'cursor': 'pointer',
    'marginLeft': 'auto'
}

FILTER_DISPLAY_STYLE = {
    'display': 'flex',
    'alignItems': 'center',
    'gap': '10px',
    'marginRight': '20px'
}

FILTER_TAG_STYLE = {
    'backgroundColor': COLORS['BG_LIGHT'],
    'padding': '5px 10px',
    'borderRadius': '4px',
    'marginRight': '10px'
}

# Chart container styles
CHART_CONTAINER_STYLE = {
    'margin': '20px 0',
    'padding': '15px',
    'backgroundColor': COLORS['BG_MEDIUM'],
    'borderRadius': '8px'
}

# Image styles
IMAGE_GRID_STYLE = {
    'display': 'flex',
    'flexWrap': 'wrap',
    'justifyContent': 'center',
    'gap': '20px',
    'margin': '20px 0'
}

IMAGE_ITEM_STYLE = {
    'display': 'flex',
    'flexDirection': 'column',
    'alignItems': 'center',
    'margin': '10px'
}

IMAGE_STYLE = {
    'width': '150px',
    'objectFit': 'cover',
    'margin': '5px',
    'border': f"2px solid {COLORS['BORDER_DARK']}"
}

# Text styles
NO_DATA_STYLE = {
    'color': COLORS['TEXT_MUTED'],
    'fontStyle': 'italic',
    'textAlign': 'center',
    'marginTop': '20px'
}

# Date picker container style
DATE_PICKER_CONTAINER_STYLE = {
    'textAlign': 'center',
    'margin': '20px'
}

# Platform-specific filter styles
PLATFORM_FILTER_STYLE = {
    'backgroundColor': COLORS['SECONDARY'],
    'padding': '5px 10px',
    'borderRadius': '4px',
    'marginRight': '10px'
}

# Language filter style
LANGUAGE_FILTER_STYLE = {
    'backgroundColor': COLORS['ACCENT'],
    'padding': '5px 10px',
    'borderRadius': '4px',
    'marginRight': '10px'
}

# Details container style
DETAILS_CONTAINER_STYLE = {
    'backgroundColor': COLORS['BG_MEDIUM'],
    'padding': '15px',
    'borderRadius': '8px',
    'margin': '10px'
}

# Detail item style
DETAIL_ITEM_STYLE = {
    'margin': '5px 0'
}

# Filter header style
FILTER_HEADER_STYLE = {
    'display': 'flex',
    'alignItems': 'center'
}

# Tabs container style
TABS_CONTAINER_STYLE = {
    'margin': '20px 0'
}
