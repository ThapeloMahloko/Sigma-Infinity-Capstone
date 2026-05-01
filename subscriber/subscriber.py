from __future__ import annotations

import json
import os
import time
from datetime import datetime

import paho.mqtt.client as mqtt

try:
    from Database.Sql import SensorReading, get_session, init_db
except ImportError:
    from Sql import SensorReading, get_session, init_db


BROKER_HOST = os.getenv("SMART_FARM_BROKER_HOST", "broker.hivemq.com")
BROKER_PORT = int(os.getenv("SMART_FARM_BROKER_PORT", "1883"))
TEAM_ID = os.getenv("SMART_FARM_TEAM_ID", "team01")
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
    sensor_name, field_name = TOPIC_MAP.get(suffix, (suffix, suffix))
    parsed_value = parse_value(field_name, payload_text)

    reading_kwargs = {
        "topic": topic,
        "sensor_name": sensor_name,
        "raw_payload": payload_text,
    }

    if field_name in {"motion_detection", "pump_status", "fan_status"}:
        reading_kwargs[field_name] = bool(parsed_value)
        reading_kwargs["value"] = 1.0 if parsed_value else 0.0
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
        reading_kwargs["value"] = float(parsed_value)
    else:
        reading_kwargs["value"] = None

    return SensorReading(**reading_kwargs)


def save_message(topic: str, payload_text: str) -> None:
    init_db()
    reading = build_reading(topic, payload_text)

    with get_session() as session:
        session.add(reading)
        session.commit()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] {topic} -> {payload_text}")


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

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="SmartFarm_Receiver")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    print(f"Connecting to broker {BROKER_HOST}:{BROKER_PORT} ...")
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