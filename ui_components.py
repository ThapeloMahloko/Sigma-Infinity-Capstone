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

IS_DARK_MODE = [True]

def get_current_colors():
    if IS_DARK_MODE[0]:
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
    else:
        return {
            "bg": COLOR_BACKGROUND_LIGHT,
            "surface": COLOR_PRIMARY_LIGHT,
            "surface_2": COLOR_SECONDARY_LIGHT,
            "accent": COLOR_ACCENT_LIGHT_MODE,
            "accent_soft": COLOR_ACCENT_LIGHT_MODE_LIGHT,
            "text": COLOR_TEXT_LIGHT,
            "text_muted": COLOR_TEXT_MUTED_LIGHT,
            "border": COLOR_BORDER_LIGHT,
        }

dynamic_css = pn.pane.HTML("")

def update_dynamic_css():
    colors = get_current_colors()
    dynamic_css.object = f"""
    <style>
    body {{ background-color: {colors['bg']} !important; }}
    .sidebar {{ background: {colors['surface_2']} !important; border-right: 1px solid {colors['border']} !important; }}
    .hero {{ background: linear-gradient(135deg, {colors['surface']}, {colors['bg']}) !important; }}
    .sensor-card {{ background: {colors['surface']} !important; border: 1px solid {colors['border']} !important; }}
    .section-box {{ background: {colors['surface']} !important; border: 1px solid {colors['border']} !important; }}
    h1,h2,h3,p,div {{ color: {colors['text']} !important; }}
    .bk-input, .bk-input-group .bk-input, select.bk-input {{ background-color: {colors['surface']} !important; color: {colors['text']} !important; border: 1px solid {colors['border']} !important; }}
    .bk-input option, select.bk-input option {{ background-color: {colors['surface']} !important; color: {colors['text']} !important; }}
    </style>
    """
update_dynamic_css()



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

    colors = get_current_colors()
    card_style = f"background: {colors['surface']}; border-radius: 18px; padding: 20px; border: 1px solid {colors['border']}; min-height: 120px; display: flex; flex-direction: column; justify-content: center;"
    label_style = f"font-size:14px;color:{colors['text_muted']}; text-transform: uppercase;"
    value_style = f"font-size:48px;font-weight:bold;color:{colors['text']}; line-height: 1.2;"
    status_val_style = f"font-size:20px;font-weight:600;color:{colors['text']};margin-top:8px;"

    temp_card.object = f"""
    <div style='{card_style}'>
        <div style='{label_style}'>TEMPERATURE</div>
        <div style='{value_style}'>{values['temperature']:.1f}°C</div>
    </div>
    """

    humidity_card.object = f"""
    <div style='{card_style}'>
        <div style='{label_style}'>HUMIDITY</div>
        <div style='{value_style}'>{values['humidity']:.1f}%</div>
    </div>
    """

    soil_card.object = f"""
    <div style='{card_style}'>
        <div style='{label_style}'>SOIL MOISTURE</div>
        <div style='{value_style}'>{values['soil']:.1f}%</div>
    </div>
    """

    water_card.object = f"""
    <div style='{card_style}'>
        <div style='{label_style}'>WATER LEVEL</div>
        <div style='{value_style}'>{values['water']:.1f}%</div>
    </div>
    """

    light_card.object = f"""
    <div style='{card_style}'>
        <div style='{label_style}'>LIGHT</div>
        <div style='{value_style}'>{values['light']:.1f}%</div>
    </div>
    """

    rain_card.object = f"""
    <div style='{card_style}'>
        <div style='{label_style}'>RAIN</div>
        <div style='{value_style}'>{values['rain']:.1f}%</div>
    </div>
    """

    fan_card.object = f"""
    <div style='{card_style}'>
        <div style='{label_style}'>FAN SPEED</div>
        <div style='{value_style}'>{int(values['fan_speed'])}</div>
    </div>
    """

    status_card.object = f"""
    <div style='{card_style}'>
        <div style='{label_style}'>SYSTEM STATUS</div>
        <div style='{status_val_style}'>
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

hover = HoverTool(tooltips=[("Time", "@x{%F %T}"), ("Value", "@y")], formatters={"@x": "datetime"})
plot.add_tools(hover)

def update_plot_colors():
    colors = get_current_colors()
    plot.background_fill_color = colors["surface"]
    plot.border_fill_color = colors["surface"]
    plot.title.text_color = colors["text"]
    plot.xaxis.major_label_text_color = colors["text"]
    plot.yaxis.major_label_text_color = colors["text"]
    plot.renderers[0].glyph.line_color = colors["accent"]
    plot.renderers[1].glyph.fill_color = colors["accent"]
    plot.renderers[1].glyph.line_color = colors["accent"]

update_plot_colors()



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
        update_plot_colors()

    doc.add_next_tick_callback(apply_graph_refresh)


sensor_selector.param.watch(lambda event: schedule_graph_refresh(), "value")

# =========================================================
# NAVBAR / HERO
# =========================================================

hero = pn.pane.HTML("")

def refresh_hero():
    colors = get_current_colors()
    hero.object = f"""
    <div class='hero'>
    <div style='font-size:14px;letter-spacing:4px;color:{colors['text_muted']};'>LIVE SMART AGRICULTURE</div>
    <div style='font-size:56px;font-weight:800;color:{colors['text']};margin-top:10px;'>Smart Farm Dashboard</div>
    <div style='font-size:18px;color:{colors['text_muted']};margin-top:15px;'>Real-time monitoring and intelligent automation</div>
    </div>
    """

refresh_hero()
