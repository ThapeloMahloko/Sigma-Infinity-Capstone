# =========================================================
# MQTT HANDLER
# =========================================================

import paho.mqtt.client as mqtt
import threading
from datetime import datetime
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, SENSOR_TOPICS
from database import save_sensor_data
from pages.telegram import send_telegram_message

# =========================================================
# GLOBAL STATE
# =========================================================

sensor_values = {key: 0.0 for key in SENSOR_TOPICS.values()}
alarm_status = "DISARMED"
feed_status = "CLOSED"
motion_status = "NO MOTION"

_last_water_warning = 0

data_lock = threading.Lock()
active_doc = None

client = mqtt.Client()

# =========================================================
# CALLBACKS
# =========================================================

def on_connect(client, userdata, flags, rc):
    print("MQTT CONNECTED")
    client.subscribe(MQTT_TOPIC)
    send_telegram_message("✅ Smart Farm Connected (MQTT)")

def on_message(client, userdata, msg):
    global alarm_status, feed_status, motion_status

    topic = msg.topic
    payload = msg.payload.decode()

    print(f"{topic}: {payload}")

    if topic in SENSOR_TOPICS:
        try:
            value = float(payload)
        except Exception:
            return

        sensor_key = SENSOR_TOPICS[topic]
        timestamp_value = datetime.now()

        from ui_components import record_sensor_sample

        record_sensor_sample(sensor_key, value, timestamp_value)

        with data_lock:
            sensor_values[sensor_key] = value

        save_sensor_data(sensor_key, value)
        schedule_ui_refresh()
        
        # Water level warning
        global _last_water_warning
        if sensor_key == "water":
            now_ts = timestamp_value.timestamp()
            # Send warning if water is below 20%, but limit to once per hour
            if value < 20.0 and (now_ts - _last_water_warning) > 3600:
                send_telegram_message(f"💧 WARNING: Water level is low ({value:.1f}%)")
                _last_water_warning = now_ts
                
        return

    if topic == "sitech/farm/alarm_status":
        if payload != alarm_status:
            send_telegram_message(f"🚨 Alarm Status: {payload}")
        alarm_status = payload
    elif topic == "sitech/farm/feed_status":
        feed_status = payload
    elif topic == "sitech/farm/alert":
        if payload != motion_status:
            if "MOTION" in payload:
                send_telegram_message(f"⚠️ Motion Detected!")
        motion_status = payload

    schedule_ui_refresh()

def _ui_refresh_callback():
    # Import here to avoid circular dependency
    from ui_components import refresh_cards, refresh_graph
    refresh_cards()
    refresh_graph()

def schedule_ui_refresh():
    return

# =========================================================
# MQTT SETUP
# =========================================================

def init_mqtt():
    try:
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print(f"✓ MQTT connected to {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"⚠ MQTT connection failed: {e}")
        print("  App will continue with default sensor values.")
        print("  To enable MQTT, set MQTT_BROKER env variable or configure credentials.")

def send_mqtt(topic, message):
    client.publish(topic, message)
    print(f"SENT -> {topic}: {message}")

def set_active_doc(doc):
    global active_doc
    active_doc = doc
