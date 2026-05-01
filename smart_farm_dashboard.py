import panel as pn
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlalchemy as sa
from sqlalchemy.orm import Session as SASession
import hvplot.pandas
import holoviews as hv

# Enable extensions
pn.extension('tabulator', 'plotly', 'vega')
hv.extension('plotly')

# Setup database connection
engine = sa.create_engine('sqlite:///sensor_data.db', echo=False)

class SensorReading:
    pass

# Configuration
DARK_MODE_CSS = """
:root {
    --bs-body-bg: #1a1a1a;
    --bs-body-color: #e0e0e0;
    --bs-primary: #4a9eff;
    --bs-secondary: #6c757d;
    --bs-danger: #ff6b6b;
    --bs-warning: #ffc93d;
    --bs-success: #51cf66;
}

body {
    background-color: #0d0d0d;
    color: #e0e0e0;
}

.dark-card {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 20px;
    color: #e0e0e0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

.dark-metric-value {
    font-size: 2.5em;
    font-weight: bold;
    color: #4a9eff;
    text-shadow: 0 0 10px rgba(74, 158, 255, 0.3);
}

.dark-metric-label {
    font-size: 0.9em;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 5px;
}

.dark-header {
    background: linear-gradient(135deg, #1a3a52 0%, #0d1f2d 100%);
    border-bottom: 2px solid #4a9eff;
    padding: 20px;
    border-radius: 8px;
    color: #4a9eff;
}

.dark-chart-container {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 15px;
}

.dark-toggle {
    background-color: #2a2a2a;
    border: 1px solid #444;
    color: #e0e0e0;
}

.dark-toggle:hover {
    background-color: #3a3a3a;
}
"""

# Dark mode theme colors
DARK_PALETTE = {
    'primary': '#4a9eff',
    'secondary': '#6c757d',
    'success': '#51cf66',
    'warning': '#ffc93d',
    'danger': '#ff6b6b',
    'bg_light': '#1e1e1e',
    'bg_darker': '#0d0d0d',
    'text_light': '#e0e0e0',
    'text_muted': '#999',
}

# Load and process data
def load_sensor_data():
    """Load sensor data from database"""
    try:
        df = pd.read_sql_table('sensor_readings', engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def get_latest_readings(df):
    """Get the most recent sensor readings"""
    if df.empty:
        return {col: 'N/A' for col in df.columns}
    return df.iloc[-1]

def create_metric_card(label, value, unit, icon_color='#4a9eff'):
    """Create a styled metric card"""
    formatted_value = f"{value:.1f}" if isinstance(value, (int, float)) else str(value)
    
    return pn.pane.HTML(f"""
    <div class="dark-card" style="text-align: center;">
        <div style="color: {icon_color}; font-size: 2em; margin-bottom: 10px;">⚡</div>
        <div class="dark-metric-value">{formatted_value}</div>
        <div class="dark-metric-label">{label}</div>
        <div style="color: {DARK_PALETTE['text_muted']}; font-size: 0.8em; margin-top: 5px;">{unit}</div>
    </div>
    """)

def create_dashboard():
    """Build the main dashboard"""
    
    # Add custom CSS
    pn.template.css = DARK_MODE_CSS
    
    # Load data
    df = load_sensor_data()
    
    if df.empty:
        return pn.pane.HTML("<h2 style='color: #ff6b6b;'>No sensor data available</h2>")
    
    # Get latest readings
    latest = get_latest_readings(df)
    
    # Create header
    header = pn.pane.HTML(f"""
    <div class="dark-header">
        <h1 style="margin: 0; color: #4a9eff;">🌾 Smart Farm Dashboard</h1>
        <p style="margin: 5px 0 0 0; color: #999;">Real-time monitoring • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """)
    
    # Current metrics row
    metrics_row = pn.Row(
        create_metric_card('Temperature', latest.get('temperature', 0), '°C', '#ff6b6b'),
        create_metric_card('Humidity', latest.get('humidity', 0), '%', '#4a9eff'),
        create_metric_card('Light', latest.get('ambient_light', 0), 'lux', '#ffc93d'),
        create_metric_card('Water Level', latest.get('water_level', 0), '%', '#51cf66'),
        name='Current Readings'
    )
    
    # Time series data (last 24 hours)
    last_24h = df[df['timestamp'] >= datetime.now() - timedelta(hours=24)]
    
    if not last_24h.empty:
        # Temperature chart
        temp_chart = last_24h.hvplot(
            x='timestamp', y='temperature', 
            title='Temperature Trend (24h)',
            line_width=2, color=DARK_PALETTE['primary'],
            responsive=True, height=300
        ).opts(
            bgcolor=DARK_PALETTE['bg_light'],
            fgcolor=DARK_PALETTE['text_light']
        )
        
        # Humidity chart
        humidity_chart = last_24h.hvplot(
            x='timestamp', y='humidity',
            title='Humidity Trend (24h)',
            line_width=2, color=DARK_PALETTE['success'],
            responsive=True, height=300
        ).opts(
            bgcolor=DARK_PALETTE['bg_light'],
            fgcolor=DARK_PALETTE['text_light']
        )
        
        # Light levels chart
        light_chart = last_24h.hvplot(
            x='timestamp', y='ambient_light',
            title='Ambient Light (24h)',
            line_width=2, color=DARK_PALETTE['warning'],
            responsive=True, height=300
        ).opts(
            bgcolor=DARK_PALETTE['bg_light'],
            fgcolor=DARK_PALETTE['text_light']
        )
        
        charts_row = pn.Row(
            pn.pane.HoloViews(temp_chart, sizing_mode='stretch_width'),
            pn.pane.HoloViews(humidity_chart, sizing_mode='stretch_width'),
            pn.pane.HoloViews(light_chart, sizing_mode='stretch_width'),
            name='Time Series'
        )
    else:
        charts_row = pn.pane.HTML("<p style='color: #ff6b6b;'>Insufficient data for charts</p>")
    
    # Statistics table
    stats_data = {
        'Metric': ['Temperature', 'Humidity', 'Light Level', 'Water Level', 'Soil Moisture'],
        'Min': [
            f"{df['temperature'].min():.1f}°C",
            f"{df['humidity'].min():.1f}%",
            f"{df['ambient_light'].min():.1f} lux",
            f"{df['water_level'].min():.1f}%" if not df['water_level'].isna().all() else 'N/A',
            f"{df['soil_moisture'].min():.1f}%" if not df['soil_moisture'].isna().all() else 'N/A',
        ],
        'Avg': [
            f"{df['temperature'].mean():.1f}°C",
            f"{df['humidity'].mean():.1f}%",
            f"{df['ambient_light'].mean():.1f} lux",
            f"{df['water_level'].mean():.1f}%" if not df['water_level'].isna().all() else 'N/A',
            f"{df['soil_moisture'].mean():.1f}%" if not df['soil_moisture'].isna().all() else 'N/A',
        ],
        'Max': [
            f"{df['temperature'].max():.1f}°C",
            f"{df['humidity'].max():.1f}%",
            f"{df['ambient_light'].max():.1f} lux",
            f"{df['water_level'].max():.1f}%" if not df['water_level'].isna().all() else 'N/A',
            f"{df['soil_moisture'].max():.1f}%" if not df['soil_moisture'].isna().all() else 'N/A',
        ],
    }
    
    stats_df = pd.DataFrame(stats_data)
    stats_table = pn.widgets.Tabulator(
        stats_df,
        name='Statistics',
        disabled=True,
        theme='dark'
    )
    
    # Raw data viewer
    data_table = pn.widgets.Tabulator(
        df.tail(50).sort_index(ascending=False),
        name='Recent Data',
        theme='dark',
        height=400
    )
    
    # Assemble dashboard
    dashboard = pn.template.BootstrapTemplate(
        title='Smart Farm Dashboard',
        header_background=DARK_PALETTE['bg_darker'],
        sidebar_width=0
    )
    
    dashboard.main[:] = [
        header,
        pn.layout.Divider(height=10),
        metrics_row,
        pn.layout.Divider(height=10),
        pn.Tabs(
            ('Charts', charts_row),
            ('Statistics', stats_table),
            ('Data Viewer', data_table)
        ),
    ]
    
    return dashboard

if __name__ == '__main__':
    dashboard = create_dashboard()
    dashboard.show(port=5006, threaded=True)
