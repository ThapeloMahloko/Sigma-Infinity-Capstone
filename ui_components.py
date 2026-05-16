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
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_BACKGROUND,
    COLOR_PRIMARY_LIGHT, COLOR_SECONDARY_LIGHT, COLOR_ACCENT_LIGHT_MODE,
    COLOR_ACCENT_LIGHT_MODE_LIGHT, COLOR_TEXT_LIGHT, COLOR_TEXT_MUTED_LIGHT,
    COLOR_BORDER_LIGHT, COLOR_BACKGROUND_LIGHT
)

# =========================================================
# PANEL SETUP
# =========================================================

pn.extension("tabulator", sizing_mode="stretch_width")

def get_current_colors():
    return {
        "bg": COLOR_BACKGROUND,
        "surface": COLOR_PRIMARY,
        "surface_2": COLOR_SECONDARY,
        "accent": COLOR_ACCENT,
        "accent_soft": COLOR_ACCENT_LIGHT,
        "text": COLOR_TEXT,
        "text_muted": COLOR_TEXT_MUTED,
        "border": COLOR_BORDER,
    }


# CSS STYLING
# =========================================================

pn.config.raw_css.append("""

body {
    background-color: #071411 !important;
}

.sidebar {
    background: #0b1f1a;
    border-right: 1px solid #16352d;
    padding: 20px;
}

.hero {
    background: linear-gradient(135deg,#0d2f25,#071411);
    border-radius: 24px;
    padding: 35px;
    margin-bottom: 20px;
}

.sensor-card {
    background: #0c1f1a;
    border-radius: 18px;
    padding: 20px;
    border: 1px solid #16352d;
}

.section-box {
    background: #0c1f1a;
    border-radius: 18px;
    padding: 20px;
    margin-top: 20px;
    border: 1px solid #16352d;
}

h1,h2,h3,p,div {
    color:white;
}

/* Match select widgets to dashboard theme */
.bk-input,
.bk-input-group .bk-input,
select.bk-input {
    background-color: #0c1f1a !important;
    color: #ffffff !important;
    border: 1px solid #16352d !important;
}

.bk-input option,
select.bk-input option {
    background-color: #0c1f1a;
    color: #ffffff;
}

/* Button Styling matching Flutter app */
.bk-btn {
    border-radius: 999px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
}

.bk-btn.bk-btn-success {
    background-color: rgba(66, 211, 146, 0.4) !important;
    border: 1px solid #42d392 !important;
    color: white !important;
}

.bk-btn.bk-btn-success:hover {
    background-color: rgba(66, 211, 146, 0.6) !important;
}

.bk-btn.bk-btn-danger {
    background-color: rgba(244, 67, 54, 0.8) !important;
    border: 1px solid #f44336 !important;
    color: white !important;
}

.bk-btn.bk-btn-danger:hover {
    background-color: rgba(244, 67, 54, 1.0) !important;
}

.bk-btn.bk-btn-warning {
    background-color: rgba(255, 152, 0, 0.8) !important;
    border: 1px solid #ff9800 !important;
    color: white !important;
}

.bk-btn.bk-btn-warning:hover {
    background-color: rgba(255, 152, 0, 1.0) !important;
}

.bk-btn.bk-btn-default {
    background-color: transparent !important;
    border: 1px solid #16352d !important;
    color: #8fb8aa !important;
}

.bk-btn.bk-btn-default:hover {
    background-color: #16352d !important;
    color: white !important;
}

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
        <div style='font-size:14px;color:var(--sf-text-muted);'>TEMPERATURE</div>
        <div style='font-size:48px;font-weight:bold;'>{values['temperature']:.1f}°C</div>
    </div>
    """

    humidity_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:var(--sf-text-muted);'>HUMIDITY</div>
        <div style='font-size:48px;font-weight:bold;'>{values['humidity']:.1f}%</div>
    </div>
    """

    soil_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:var(--sf-text-muted);'>SOIL MOISTURE</div>
        <div style='font-size:48px;font-weight:bold;'>{values['soil']:.1f}%</div>
    </div>
    """

    water_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:var(--sf-text-muted);'>WATER LEVEL</div>
        <div style='font-size:48px;font-weight:bold;'>{values['water']:.1f}%</div>
    </div>
    """

    light_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:var(--sf-text-muted);'>LIGHT</div>
        <div style='font-size:48px;font-weight:bold;'>{values['light']:.1f}%</div>
    </div>
    """

    rain_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:var(--sf-text-muted);'>RAIN</div>
        <div style='font-size:48px;font-weight:bold;'>{values['rain']:.1f}%</div>
    </div>
    """

    fan_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:var(--sf-text-muted);'>FAN SPEED</div>
        <div style='font-size:48px;font-weight:bold;'>{int(values['fan_speed'])}</div>
    </div>
    """

    status_card.object = f"""
    <div class='sensor-card'>
        <div style='font-size:14px;color:var(--sf-text-muted);'>SYSTEM STATUS</div>
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

colors = get_current_colors()

plot = figure(
    height=400,
    sizing_mode="stretch_width",
    x_axis_type="datetime",
    background_fill_color=colors["surface"],
    border_fill_color=colors["surface"]
)

plot.line(x="x", y="y", source=source, line_width=3, color=colors["accent"])
plot.circle(x="x", y="y", source=source, size=8, color=colors["accent"])

plot.title.text = "Live Sensor Trends"
plot.title.text_color = colors["text"]
plot.xaxis.major_label_text_color = colors["text"]
plot.yaxis.major_label_text_color = colors["text"]

hover = HoverTool(tooltips=[("Time", "@x{%F %T}"), ("Value", "@y")], formatters={"@x": "datetime"})
plot.add_tools(hover)

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
    doc = pn.state.curdoc
    if doc is None:
        refresh_graph()
        return

    def apply_graph_refresh():
        refresh_graph()

    doc.add_next_tick_callback(apply_graph_refresh)


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
