# =========================================================
# MQTT HANDLER
# =========================================================
"""
MQTT Handler Module.

This module sets up the MQTT client, handles connections, processes incoming messages,
updates global state variables, saves sensor data, and triggers UI refreshes.
"""

import paho.mqtt.client as mqtt
import threading
from datetime import datetime
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, SENSOR_TOPICS
from database import save_sensor_data

# =========================================================
# GLOBAL STATE
# =========================================================

# Dictionary to hold the latest values for all sensors, initialized to 0.0
sensor_values = {key: 0.0 for key in SENSOR_TOPICS.values()}

# System statuses
alarm_status = "DISARMED"
feed_status = "CLOSED"
motion_status = "NO MOTION"

# Lock for thread-safe operations on shared state
data_lock = threading.Lock()
active_doc = None

# Initialize the MQTT client instance
client = mqtt.Client()

# =========================================================
# CALLBACKS
# =========================================================

def on_connect(client, userdata, flags, rc) -> None:
    """
    Callback triggered when the MQTT client successfully connects to the broker.

    Args:
        client: The MQTT client instance.
        userdata: The private user data as set in Client() or user_data_set().
        flags: Response flags sent by the broker.
        rc (int): The connection result.
    """
    if rc == 0:
        print("MQTT CONNECTED")
        # Subscribe to all subtopics under the main MQTT_TOPIC
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"MQTT CONNECTION FAILED with return code {rc}")

def on_message(client, userdata, msg) -> None:
    """
    Callback triggered when an MQTT message is received on a subscribed topic.

    Args:
        client: The MQTT client instance.
        userdata: The private user data.
        msg: An instance of MQTTMessage containing topic and payload.
    """
    global alarm_status, feed_status, motion_status

    topic = msg.topic
    
    try:
        payload = msg.payload.decode('utf-8')
    except UnicodeDecodeError:
        print(f"Error decoding payload for topic {topic}")
        return

    print(f"{topic}: {payload}")

    # Check if the topic is a known sensor topic
    if topic in SENSOR_TOPICS:
        try:
            value = float(payload)
        except ValueError:
            print(f"Invalid float payload '{payload}' for topic {topic}")
            return

        sensor_key = SENSOR_TOPICS[topic]
        timestamp_value = datetime.now()

        # Import here to avoid circular dependency
        from ui_components import record_sensor_sample
        record_sensor_sample(sensor_key, value, timestamp_value)

        # Safely update the global dictionary
        with data_lock:
            sensor_values[sensor_key] = value

        save_sensor_data(sensor_key, value)
        schedule_ui_refresh()
        return

    # Handle status topics
    if topic == "sitech/farm/alarm_status":
        alarm_status = payload
    elif topic == "sitech/farm/feed_status":
        feed_status = payload
    elif topic == "sitech/farm/alert":
        motion_status = payload

    schedule_ui_refresh()

def _ui_refresh_callback() -> None:
    """Internal callback to refresh UI components."""
    # Import here to avoid circular dependency
    from ui_components import refresh_cards, refresh_graph
    try:
        refresh_cards()
        refresh_graph()
    except Exception as e:
        print(f"Error during UI refresh: {e}")

def schedule_ui_refresh() -> None:
    """
    Schedules a UI refresh by triggering Panel callbacks.
    Currently a placeholder; Panel's periodic callbacks handle updates in main.py.
    """
    return

# =========================================================
# MQTT SETUP
# =========================================================

def init_mqtt() -> None:
    """
    Initializes the MQTT client, sets up callbacks, and starts the background loop.
    """
    try:
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        # Start a background thread to handle network traffic
        client.loop_start()
        print(f"MQTT connected to {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"MQTT connection failed: {e}")
        print("  App will continue with default sensor values.")
        print("  To enable MQTT, set MQTT_BROKER env variable or configure credentials.")

def send_mqtt(topic: str, message: str) -> None:
    """
    Publishes a message to a specific MQTT topic.

    Args:
        topic (str): The destination topic.
        message (str): The payload to send.
    """
    try:
        client.publish(topic, message)
        print(f"SENT -> {topic}: {message}")
    except Exception as e:
        print(f"Failed to send MQTT message: {e}")

def set_active_doc(doc) -> None:
    """
    Sets the active Panel document for scheduling callbacks.

    Args:
        doc: The Panel curdoc (current document).
    """
    global active_doc
    active_doc = doc
