# =========================================================
# ANALYTICS PAGE
# =========================================================

import panel as pn
from datetime import datetime, timedelta
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
import pandas as pd

from config import SENSOR_LABELS, SENSOR_UNITS, COLOR_PRIMARY, COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_ACCENT_LIGHT
from database import Session, SensorData
from utils import build_stats_html, get_range_window

# =========================================================
# ANALYTICS WIDGETS
# =========================================================

analytics_sensor = pn.widgets.Select(
    name="Sensor",
    options={SENSOR_LABELS[key]: key for key in SENSOR_LABELS},
    value="temperature"
)

analytics_range = pn.widgets.Select(
    name="Range",
    options=[
        "Last 1 hour",
        "Last 2 hours",
        "Last 4 hours",
        "Last 8 hours",
        "Last 16 hours",
        "Last 24 hours",
        "Last 7 days",
        "Last 30 days",
        "Custom"
    ],
    value="Last 24 hours"
)

analytics_start = pn.widgets.DatetimePicker(
    name="Start Date/Time",
    value=datetime.now() - timedelta(hours=24)
)

analytics_end = pn.widgets.DatetimePicker(
    name="End Date/Time",
    value=datetime.now()
)

analytics_apply_btn = pn.widgets.Button(
    name="Apply Filters",
    button_type="success"
)

analytics_status = pn.pane.Markdown("Ready.")
analytics_stats = pn.pane.HTML(width=1000)

# =========================================================
# ANALYTICS PLOT
# =========================================================

analytics_plot_source = ColumnDataSource(data=dict(x=[], y=[]))

analytics_plot = figure(
    height=380,
    sizing_mode="stretch_width",
    x_axis_type="datetime",
    background_fill_color=COLOR_PRIMARY,
    border_fill_color=COLOR_PRIMARY
)

analytics_plot.line(x="x", y="y", source=analytics_plot_source, line_width=3, color=COLOR_ACCENT)
analytics_plot.scatter(x="x", y="y", source=analytics_plot_source, size=6, color=COLOR_ACCENT_LIGHT)

analytics_plot.title.text = "Historical Sensor Trend"
analytics_plot.title.text_color = COLOR_TEXT
analytics_plot.xaxis.major_label_text_color = COLOR_TEXT
analytics_plot.yaxis.major_label_text_color = COLOR_TEXT
analytics_plot.xaxis.axis_label_text_color = COLOR_TEXT
analytics_plot.yaxis.axis_label_text_color = COLOR_TEXT
analytics_plot.grid.grid_line_alpha = 0.18

analytics_plot_hover = HoverTool(
    tooltips=[("Time", "@x{%F %T}"), ("Value", "@y{0.00}")],
    formatters={"@x": "datetime"}
)
analytics_plot.add_tools(analytics_plot_hover)

# =========================================================
# ANALYTICS TABLE
# =========================================================

analytics_table = pn.widgets.Tabulator(
    pd.DataFrame(),
    height=500,
    sizing_mode="stretch_width"
)

# =========================================================
# ANALYTICS FUNCTIONS
# =========================================================

def sync_datetime_pickers(event=None):
    if analytics_range.value == "Custom":
        return

    start_time, end_time = get_range_window(analytics_range.value, analytics_start, analytics_end)
    analytics_start.value = start_time
    analytics_end.value = end_time

def fetch_sensor_dataframe(sensor_key, start_time, end_time):
    local_session = Session()

    try:
        rows = local_session.query(SensorData).filter(
            SensorData.sensor == sensor_key,
            SensorData.timestamp >= start_time,
            SensorData.timestamp <= end_time
        ).order_by(SensorData.timestamp.asc()).all()

        data = [{
            "Sensor": row.sensor,
            "Value": row.value,
            "Timestamp": row.timestamp
        } for row in rows]

        return pd.DataFrame(data)
    finally:
        local_session.close()

def update_analytics(event=None):
    sensor_key = analytics_sensor.value
    start_time, end_time = get_range_window(analytics_range.value, analytics_start, analytics_end)

    if start_time is None or end_time is None:
        analytics_status.object = "Please provide both start and end date/time for a custom range."
        return

    if start_time > end_time:
        analytics_status.object = "Start date/time must be before end date/time."
        return

    df = fetch_sensor_dataframe(sensor_key, start_time, end_time)

    analytics_table.value = df.sort_values(by="Timestamp", ascending=False) if not df.empty else pd.DataFrame(columns=["Sensor", "Value", "Timestamp"])

    if not df.empty:
        analytics_plot_source.data = {
            "x": pd.to_datetime(df["Timestamp"]).tolist(),
            "y": df["Value"].astype(float).tolist(),
        }
    else:
        analytics_plot_source.data = {"x": [], "y": []}

    analytics_plot.yaxis.axis_label = f"{SENSOR_LABELS[sensor_key]} ({SENSOR_UNITS[sensor_key]})"
    analytics_stats.object = build_stats_html(df, sensor_key)

    analytics_status.object = (
        f"Loaded {len(df)} records for {SENSOR_LABELS[sensor_key]} "
        f"from {start_time:%Y-%m-%d %H:%M} to {end_time:%Y-%m-%d %H:%M}."
    )

analytics_range.param.watch(sync_datetime_pickers, "value")
analytics_sensor.param.watch(update_analytics, "value")
analytics_apply_btn.on_click(update_analytics)

sync_datetime_pickers()

def _initialize_analytics_view():
    update_analytics()

pn.state.onload(_initialize_analytics_view)

# =========================================================
# ANALYTICS PAGE LAYOUT
# =========================================================

analytics_page = pn.Column(
    pn.pane.HTML("""
    <div class='hero'>
    <div style='font-size:14px;letter-spacing:4px;color:%s;'>ANALYTICS</div>
    <div style='font-size:52px;font-weight:800;color:white;margin-top:10px;'>Historical Analytics</div>
    </div>
    """ % COLOR_TEXT_MUTED),

    pn.Column(
        pn.Row(
            analytics_sensor,
            analytics_range,
            analytics_apply_btn
        ),
        pn.Row(
            analytics_start,
            analytics_end
        ),
        analytics_status,
        css_classes=["section-box"]
    ),

    pn.Column(
        analytics_plot,
        css_classes=["section-box"]
    ),

    analytics_stats,

    pn.Column(
        analytics_table,
        css_classes=["section-box"]
    )
)