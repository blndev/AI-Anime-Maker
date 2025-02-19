"""
Theme and layout styles for the analytics dashboard.
"""

# Theme settings for plotly charts
PLOTLY_TEMPLATE = 'plotly_dark'
LAYOUT_THEME = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'hoverlabel': {
        'bgcolor': 'rgba(45, 45, 45, 0.9)',  # Dark semi-transparent background
        'font_size': 12,
        'font_color': '#FFFFFF'  # White text
    }
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

# Filter styles
FILTER_CONTAINER_STYLE = {
    'display': 'flex',
    'justifyContent': 'space-between',
    'alignItems': 'center',
    'margin': '20px',
    'padding': '10px',
    'backgroundColor': '#2C3E50',
    'borderRadius': '4px'
}

FILTER_BUTTON_STYLE = {
    'backgroundColor': '#4CAF50',
    'color': 'white',
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
    'backgroundColor': '#34495E',
    'padding': '5px 10px',
    'borderRadius': '4px',
    'marginRight': '10px'
}

# Chart container styles
CHART_CONTAINER_STYLE = {
    'margin': '20px 0',
    'padding': '15px',
    'backgroundColor': '#2C3E50',
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
    'border': '2px solid #333'
}

# Text styles
NO_DATA_STYLE = {
    'color': '#95A5A6',
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
    'backgroundColor': '#2980B9',
    'padding': '5px 10px',
    'borderRadius': '4px',
    'marginRight': '10px'
}

# Language filter style
LANGUAGE_FILTER_STYLE = {
    'backgroundColor': '#8E44AD',
    'padding': '5px 10px',
    'borderRadius': '4px',
    'marginRight': '10px'
}

# Details container style
DETAILS_CONTAINER_STYLE = {
    'backgroundColor': '#2C3E50',
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
