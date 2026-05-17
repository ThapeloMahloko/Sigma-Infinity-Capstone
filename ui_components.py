# =========================================================
# UI COMPONENTS
# =========================================================

import panel as pn
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from collections import deque
from config import (
    SENSOR_LABELS, SENSOR_UNITS, MAX_POINTS,
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, COLOR_ACCENT_LIGHT,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_BACKGROUND
)

# =========================================================
# PANEL SETUP
# =========================================================

pn.extension("tabulator", sizing_mode="stretch_width")

# =========================================================
# CSS STYLING
# =========================================================

pn.config.raw_css.append(f"""
:root {{
    --sf-bg: {COLOR_BACKGROUND};
    --sf-surface: {COLOR_PRIMARY};
    --sf-surface-2: {COLOR_SECONDARY};
    --sf-accent: {COLOR_ACCENT};
    --sf-accent-soft: {COLOR_ACCENT_LIGHT};
    --sf-text: {COLOR_TEXT};
    --sf-text-muted: {COLOR_TEXT_MUTED};
    --sf-border: {COLOR_BORDER};
}}

html,
body,
.bk-root {{
    background:
        radial-gradient(circle at top, rgba(79, 209, 165, 0.16), transparent 28%),
        linear-gradient(180deg, var(--sf-bg) 0%, #050b11 75%);
    color: var(--sf-text);
}}

body {{
    background-color: var(--sf-bg);
}}

.sidebar {{
    background: linear-gradient(180deg, rgba(17, 35, 52, 0.96), rgba(7, 17, 26, 0.98));
    border-right: 1px solid var(--sf-border);
    padding: 22px;
    box-shadow: inset -1px 0 0 rgba(255,255,255,0.03);
}}

.hero {{
    background: linear-gradient(135deg, rgba(17, 35, 52, 0.95), rgba(7, 17, 26, 0.92));
    border-radius: 28px;
    padding: 38px;
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.22);
}}

.sensor-card,
.section-box {{
    background: linear-gradient(180deg, rgba(17, 35, 52, 0.95), rgba(10, 20, 30, 0.97));
    border-radius: 18px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
}}

.section-box {{
    margin-top: 20px;
}}

h1, h2, h3, p, div {{
    color: var(--sf-text);
}}

.bk-input,
.bk-input-group .bk-input,
select.bk-input {{
    background-color: rgba(10, 20, 30, 0.96) !important;
    color: var(--sf-text) !important;
    border: 1px solid var(--sf-border) !important;
    border-radius: 12px !important;
}}

.bk-input option,
select.bk-input option {{
    background-color: var(--sf-surface);
    color: var(--sf-text);
}}

.bk-btn,
.bk-btn-group .bk-btn {{
    border-radius: 999px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background: linear-gradient(135deg, rgba(79, 209, 165, 0.22), rgba(79, 209, 165, 0.1)) !important;
    color: var(--sf-text) !important;
}}

.bk-btn:hover,
.bk-btn-group .bk-btn:hover {{
    border-color: rgba(146, 230, 199, 0.42) !important;
    box-shadow: 0 0 0 1px rgba(146, 230, 199, 0.15), 0 10px 24px rgba(0, 0, 0, 0.18);
}}

.bk-tab {{
    color: var(--sf-text-muted) !important;
}}

.bk-tab.bk-active {{
    color: var(--sf-text) !important;
    border-bottom-color: var(--sf-accent) !important;
}}

""")

# =========================================================
# LIVE DATA STORAGE
# =========================================================

sensor_series = {key: deque(maxlen=MAX_POINTS) for key in SENSOR_LABELS}
sensor_time = {key: deque(maxlen=MAX_POINTS) for key in SENSOR_LABELS}
sensor_values = {key: 0.0 for key in SENSOR_LABELS}


def record_sensor_sample(sensor_key, value, timestamp_value):
    from mqtt_handler import data_lock

    with data_lock:
        sensor_values[sensor_key] = value
        sensor_series[sensor_key].append(value)
        sensor_time[sensor_key].append(timestamp_value)

# =========================================================
# SENSOR CARDS
# =========================================================

temp_card = pn.pane.HTML(width=250)
humidity_card = pn.pane.HTML(width=250)
soil_card = pn.pane.HTML(width=250)
water_card = pn.pane.HTML(width=250)
light_card = pn.pane.HTML(width=250)
rain_card = pn.pane.HTML(width=250)
fan_card = pn.pane.HTML(width=250)
status_card = pn.pane.HTML(width=760)

# =========================================================
# UPDATE CARDS
# =========================================================

def refresh_cards():
    from mqtt_handler import alarm_status, feed_status, motion_status, data_lock

    with data_lock:
        values = dict(sensor_values)

    temp_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:{COLOR_TEXT_MUTED};'>TEMPERATURE</div>
        <div style='font-size:48px;font-weight:bold;'>{values['temperature']:.1f}°C</div>
    </div>
    """

    humidity_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:{COLOR_TEXT_MUTED};'>HUMIDITY</div>
        <div style='font-size:48px;font-weight:bold;'>{values['humidity']:.1f}%</div>
    </div>
    """

    soil_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:{COLOR_TEXT_MUTED};'>SOIL MOISTURE</div>
        <div style='font-size:48px;font-weight:bold;'>{values['soil']:.1f}%</div>
    </div>
    """

    water_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:{COLOR_TEXT_MUTED};'>WATER LEVEL</div>
        <div style='font-size:48px;font-weight:bold;'>{values['water']:.1f}%</div>
    </div>
    """

    light_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:{COLOR_TEXT_MUTED};'>LIGHT</div>
        <div style='font-size:48px;font-weight:bold;'>{values['light']:.1f}%</div>
    </div>
    """

    rain_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:{COLOR_TEXT_MUTED};'>RAIN</div>
        <div style='font-size:48px;font-weight:bold;'>{values['rain']:.1f}%</div>
    </div>
    """

    fan_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:{COLOR_TEXT_MUTED};'>FAN SPEED</div>
        <div style='font-size:48px;font-weight:bold;'>{int(values['fan_speed'])}</div>
    </div>
    """

    status_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:{COLOR_TEXT_MUTED};'>SYSTEM STATUS</div>
        <div style='font-size:20px;font-weight:600;margin-top:8px;'>
            Alarm: {alarm_status} | Feeder: {feed_status} | Motion: {motion_status}
        </div>
    </div>
    """

refresh_cards()

# =========================================================
# LIVE GRAPH
# =========================================================

source = ColumnDataSource(data=dict(x=[], y=[]))

plot = figure(
    height=400,
    sizing_mode="stretch_width",
    x_axis_type="datetime",
    background_fill_color=COLOR_PRIMARY,
    border_fill_color=COLOR_PRIMARY
)

plot.line(x="x", y="y", source=source, line_width=3)
plot.scatter(x="x", y="y", source=source, size=8)

plot.title.text = "Live Sensor Trends"
plot.title.text_color = COLOR_TEXT
plot.xaxis.major_label_text_color = COLOR_TEXT
plot.yaxis.major_label_text_color = COLOR_TEXT

hover = HoverTool(tooltips=[("Time", "@x{%F %T}"), ("Value", "@y")], formatters={"@x": "datetime"})
plot.add_tools(hover)

plot_pane = pn.pane.Bokeh(plot, sizing_mode="stretch_width")

# =========================================================
# SENSOR SELECTOR
# =========================================================

sensor_selector = pn.widgets.Select(
    name="Sensor",
    options=[SENSOR_LABELS[key] for key in SENSOR_LABELS],
    value="Temperature",
    width=200
)

# =========================================================
# REFRESH GRAPH
# =========================================================

def refresh_graph():
    from mqtt_handler import data_lock
    
    selected = sensor_selector.value
    selected_key = "temperature"

    for key, label in SENSOR_LABELS.items():
        if label == selected:
            selected_key = key
            break

    with data_lock:
        x_values = list(sensor_time[selected_key])
        y_values = list(sensor_series[selected_key])

    source.data = dict(x=x_values, y=y_values)

def schedule_graph_refresh():
    refresh_graph()


sensor_selector.param.watch(lambda event: schedule_graph_refresh(), "value")

# =========================================================
# NAVBAR / HERO
# =========================================================

hero = pn.pane.HTML("""
<div class='hero'>
<div style='font-size:14px;letter-spacing:4px;color:%s;'>LIVE SMART AGRICULTURE</div>
<div style='font-size:56px;font-weight:800;color:%s;margin-top:10px;'>Smart Farm Dashboard</div>
<div style='font-size:18px;color:%s;margin-top:15px;'>Real-time monitoring and intelligent automation</div>
</div>
""" % (COLOR_TEXT_MUTED, COLOR_TEXT, COLOR_TEXT_MUTED))
