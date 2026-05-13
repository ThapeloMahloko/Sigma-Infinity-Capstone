# =========================================================
# CONTROLS PAGE
# =========================================================

import panel as pn
from mqtt_handler import send_mqtt

# =========================================================
# CONTROLS WIDGETS
# =========================================================

fan_slider = pn.widgets.IntSlider(
    name="Fan Speed (Manual)",
    start=0,
    end=255,
    value=0,
    width=350
)

fan_on_btn = pn.widgets.Button(
    name="🌀 Fan ON (Speed 130)",
    button_type="success",
    width=200
)

fan_off_btn = pn.widgets.Button(
    name="⛔ Fan OFF",
    button_type="danger",
    width=200
)

pump_on_btn = pn.widgets.Button(
    name="💧 Pump ON",
    button_type="success"
)

pump_off_btn = pn.widgets.Button(
    name="🛑 Pump OFF",
    button_type="danger"
)

alarm_on_btn = pn.widgets.Button(
    name="🚨 Alarm ON",
    button_type="warning"
)

alarm_off_btn = pn.widgets.Button(
    name="🔕 Alarm OFF",
    button_type="danger"
)

feed_open_btn = pn.widgets.Button(
    name="🍽 Open Feeder",
    button_type="success"
)

feed_close_btn = pn.widgets.Button(
    name="🔒 Close Feeder",
    button_type="danger"
)

# =========================================================
# CALLBACKS
# =========================================================

def update_fan(event):
    send_mqtt("sitech/farm/control/fan_speed", str(event.new))

def turn_fan_on(event):
    fan_slider.value = 130
    send_mqtt("sitech/farm/control/fan_speed", "130")

def turn_fan_off(event):
    fan_slider.value = 0
    send_mqtt("sitech/farm/control/fan_speed", "0")

fan_slider.param.watch(update_fan, "value")

fan_on_btn.on_click(turn_fan_on)
fan_off_btn.on_click(turn_fan_off)

pump_on_btn.on_click(lambda e: send_mqtt("sitech/farm/control/pump", "ON"))
pump_off_btn.on_click(lambda e: send_mqtt("sitech/farm/control/pump", "OFF"))
alarm_on_btn.on_click(lambda e: send_mqtt("sitech/farm/control/alarm", "ON"))
alarm_off_btn.on_click(lambda e: send_mqtt("sitech/farm/control/alarm", "OFF"))
feed_open_btn.on_click(lambda e: send_mqtt("sitech/farm/control/feed", "OPEN"))
feed_close_btn.on_click(lambda e: send_mqtt("sitech/farm/control/feed", "CLOSE"))

# =========================================================
# CONTROLS PAGE LAYOUT
# =========================================================

controls_page = pn.Column(
    pn.pane.HTML("""
    <div class='hero'>
    <div style='font-size:14px;letter-spacing:4px;color:#8fb8aa;'>CONTROL CENTER</div>
    <div style='font-size:52px;font-weight:800;color:white;margin-top:10px;'>Farm Controls</div>
    </div>
    """),

    pn.Column(
        pn.pane.Markdown("## Fan Controls"),
        pn.Row(
            fan_on_btn,
            fan_off_btn
        ),
        fan_slider,
        css_classes=["section-box"]
    ),

    pn.Column(
        pn.pane.Markdown("## Device Controls"),
        pn.Row(pump_on_btn, pump_off_btn),
        pn.Row(alarm_on_btn, alarm_off_btn),
        pn.Row(feed_open_btn, feed_close_btn),
        css_classes=["section-box"]
    )
)
