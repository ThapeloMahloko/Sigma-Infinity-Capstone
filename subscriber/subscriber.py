from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt

# Add parent directory to path so Database module is accessible
sys.path.insert(0, str(Path(__file__).parent.parent))

from Database.Sql import SensorReading, get_session, init_db


BROKER_HOST = os.getenv("SMART_FARM_BROKER_HOST", "broker.hivemq.com")
BROKER_PORT = int(os.getenv("SMART_FARM_BROKER_PORT", "1883"))
TEAM_ID = os.getenv("SMART_FARM_TEAM_ID", "team01")
DEFAULT_CLIENT_ID = f"SmartFarm_Receiver_{socket.gethostname()}_{os.getpid()}"
CLIENT_ID = os.getenv("SMART_FARM_CLIENT_ID", DEFAULT_CLIENT_ID)
BASE_TOPIC = f"epg317e/farm/{TEAM_ID}"

TOPIC_MAP = {
    "temperature": ("temperature", "temperature"),
    "humidity": ("humidity", "humidity"),
    "soil_moisture": ("soil_moisture", "soil_moisture"),
    "light_level": ("ambient_light", "ambient_light"),
    "ambient_light": ("ambient_light", "ambient_light"),
    "water_level": ("water_level", "water_level"),
    "rain_value": ("rainfall", "rainfall"),
    "rain": ("rainfall", "rainfall"),
    "motion": ("motion_detection", "motion_detection"),
    "motion_detection": ("motion_detection", "motion_detection"),
    "ultrasonic": ("ultrasonic_distance", "ultrasonic_distance"),
    "ultrasonic_distance": ("ultrasonic_distance", "ultrasonic_distance"),
    "pump": ("pump_status", "pump_status"),
    "pump_status": ("pump_status", "pump_status"),
    "fan": ("fan_status", "fan_status"),
    "fan_status": ("fan_status", "fan_status"),
}

LEGACY_SENSOR_TOPICS = {
    "TEMPERATURE",
    "HUMIDITY",
    "SOIL_MOISTURE",
    "LIGHT_LEVEL",
    "WATER_LEVEL",
    "RAIN_VALUE",
}

# Buffer for batch-based ingestion from legacy uppercase topics.
sensor_data = {topic: None for topic in LEGACY_SENSOR_TOPICS}
received_topics = set()
ready_for_new_batch = True


def topic_suffix(topic: str) -> str:
    return topic.rsplit("/", 1)[-1].lower()


def parse_value(sensor_name: str, payload_text: str):
    normalized = payload_text.strip()

    if sensor_name in {"motion_detection", "pump_status", "fan_status"}:
        lowered = normalized.lower()
        if lowered in {"1", "true", "on", "high", "yes"}:
            return True
        if lowered in {"0", "false", "off", "low", "no"}:
            return False
        return bool(normalized)

    try:
        return float(normalized)
    except ValueError:
        return normalized


def build_reading(topic: str, payload_text: str) -> SensorReading:
    suffix = topic_suffix(topic)
    sensor_data, field_name = TOPIC_MAP.get(suffix, (suffix, suffix))
    parsed_value = parse_value(field_name, payload_text)

    reading_kwargs = {
        "timestamp": datetime.utcnow(),
    }

    if field_name in {"motion_detection", "pump_status", "fan_status"}:
        reading_kwargs[field_name] = bool(parsed_value)
    elif field_name in {
        "soil_moisture",
        "temperature",
        "humidity",
        "water_level",
        "ambient_light",
        "rainfall",
        "ultrasonic_distance",
    }:
        reading_kwargs[field_name] = float(parsed_value)

    return SensorReading(**reading_kwargs)


def save_message(topic: str, payload_text: str) -> None:
    """
    Save a message to the database with aggregation by timestamp.
    
    Merges data from the same timestamp into a single row, only updating
    fields that are currently None/NA. Preserves existing values.
    """
    init_db()
    new_reading = build_reading(topic, payload_text)
    
    with get_session() as session:
        # Round timestamp to the nearest second for aggregation
        rounded_timestamp = new_reading.timestamp.replace(microsecond=0)
        
        # Check if a reading with this timestamp already exists
        existing_reading = session.query(SensorReading).filter(
            SensorReading.timestamp == rounded_timestamp
        ).first()
        
        if existing_reading:
            # Merge data: only update fields that are None
            for field_name in [
                "soil_moisture", "temperature", "humidity", "water_level",
                "ambient_light", "rainfall", "motion_detection",
                "ultrasonic_distance", "pump_status", "fan_status"
            ]:
                existing_value = getattr(existing_reading, field_name)
                new_value = getattr(new_reading, field_name)
                # Only update if existing is None and new has a value
                if existing_value is None and new_value is not None:
                    setattr(existing_reading, field_name, new_value)
            
            session.commit()
        else:
            # Set timestamp to rounded value for consistency
            new_reading.timestamp = rounded_timestamp
            session.add(new_reading)
            session.commit()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] {topic} -> {payload_text}")


def publish_batch_to_database() -> None:
    global ready_for_new_batch, received_topics

    print("\n" + "=" * 60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] COMPLETE DATA BATCH")
    print("=" * 60)
    print(f"TEMPERATURE:   {sensor_data['TEMPERATURE']}C")
    print(f"HUMIDITY:      {sensor_data['HUMIDITY']}%")
    print(f"SOIL_MOISTURE: {sensor_data['SOIL_MOISTURE']}%")
    print(f"LIGHT_LEVEL:   {sensor_data['LIGHT_LEVEL']}%")
    print(f"WATER_LEVEL:   {sensor_data['WATER_LEVEL']}%")
    print(f"RAIN_VALUE:    {sensor_data['RAIN_VALUE']}%")
    print("=" * 60)

    for topic_name, payload_text in sensor_data.items():
        if payload_text is not None:
            save_message(topic_name, str(payload_text))

    print("Waiting 5 seconds before accepting next batch...\n")
    time.sleep(5)

    received_topics.clear()
    ready_for_new_batch = True
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ready for next batch\n")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}")
        return

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected successfully")

    subscriptions = [
        f"{BASE_TOPIC}/sensors/#",
        f"{BASE_TOPIC}/actuators/#",
        f"{BASE_TOPIC}/control/#",
        "TEMPERATURE",
        "HUMIDITY",
        "SOIL_MOISTURE",
        "LIGHT_LEVEL",
        "WATER_LEVEL",
        "RAIN_VALUE",
        "MOTION",
        "ULTRASONIC",
        "PUMP_STATUS",
        "FAN_STATUS",
    ]

    for topic in subscriptions:
        client.subscribe(topic, qos=1)


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Disconnected: {reason_code}")


def on_message(client, userdata, message):
    global ready_for_new_batch, received_topics

    if not ready_for_new_batch:
        return

    if message.topic in LEGACY_SENSOR_TOPICS:
        payload_text = message.payload.decode("utf-8", errors="replace")
        sensor_data[message.topic] = payload_text
        received_topics.add(message.topic)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message.topic}: {payload_text}")

        if len(received_topics) == len(LEGACY_SENSOR_TOPICS):
            ready_for_new_batch = False
            publish_batch_to_database()
        return

    payload_text = message.payload.decode("utf-8", errors="replace")

    try:
        parsed = json.loads(payload_text)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        for key, value in parsed.items():
            topic_name = f"{message.topic}/{key}"
            save_message(topic_name, str(value))
        return

    save_message(message.topic, payload_text)


def main() -> None:
    init_db()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    print(f"Connecting to broker {BROKER_HOST}:{BROKER_PORT} as {CLIENT_ID} ...")
    client.connect(BROKER_HOST, port=BROKER_PORT, keepalive=60)
    client.loop_start()

    print("Waiting for smart-farm sensor messages...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSubscriber stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()