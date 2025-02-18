# AI Anime Maker Analytics Dashboard

A Plotly Dash application that visualizes analytics data from the AI Anime Maker application.

## Features

- Operating System Distribution
- Browser Usage Statistics
- Mobile vs Desktop Usage
- Geographic Distribution (Continent, Country, City)
- Language Distribution

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Make sure you have access to the analytics.db file (configured in app.config)
2. Run the application:
```bash
python app.py
```
3. Open your browser and navigate to http://127.0.0.1:8050/

## Data Updates

The dashboard reads data directly from the analytics database each time it starts. No manual data updates are required.

## Charts

1. Platform Statistics
   - Operating System Distribution
   - Browser Distribution
   - Mobile vs Desktop Usage

2. Geographic Distribution
   - Distribution by Continent
   - Top 10 Countries
   - Top 10 Cities

3. Language Distribution
   - Top 10 Languages Used
