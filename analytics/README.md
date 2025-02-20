# AI Anime Maker Analytics Dashboard

A Plotly Dash application that provides comprehensive analytics and insights for the AI Anime Maker application.

## Features

### 📊 Usage Statistics
- Session timeline with daily and hourly patterns
- Platform statistics (OS, browser distribution)
- Mobile vs desktop usage analysis
- Generation success rate tracking

### 🌍 Geographic Distribution
- Interactive world map with user locations
- Continent and country-level breakdowns
- City-level population centers
- Language distribution analysis
- Filterable by region and time period

### 📸 Image Upload Analysis
- Upload and generation timeline
- Most frequently uploaded images
- Generation patterns and trends
- Image metadata statistics
- Full-size image preview capability

### 🎨 Generation Details
- Style usage distribution with percentages
- Detailed generation history
- Image search by ID or SHA1
- Generation metadata analysis

## Running the Dashboard

The analytics dashboard is now integrated with the main application. You can start it using:

1. The run.sh script menu:
```bash
./run.sh
# Select option 2 for Analytics Dashboard only
# or option 3 to run both main app and dashboard
```

2. Or directly:
```bash
python analytics_dashboard.py
```

## Data Management

- Real-time data updates from the analytics database
- Centralized filter system across all components
- Advanced search and filtering capabilities
- Comprehensive logging system

## Configuration

The dashboard uses settings from the main app.config file:
- analytics_enabled: Must be true to collect data
- analytics_db_path: Path to the SQLite database
- analytics_city_db: Optional GeoLite2 database for enhanced location data

For GeoLite2 setup, visit: https://dev.maxmind.com/geoip/geoip2/geolite2/

## Advanced Analysis

For deeper data analysis, use the Jupyter notebook:
```bash
jupyter lab Analyze_Usage.ipynb
```
