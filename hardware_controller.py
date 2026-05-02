#!/usr/bin/env python3
"""
🌱 Smart Farm - Hardware Device Controller (Python Version)
Subscribes to MQTT control topics and manages GPIO relays via RPi/Linux
"""

import os
import sys
import time
import json
import signal
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ================= CONFIGURATION =================
MQTT_BROKER = os.getenv("SMART_FARM_BROKER_HOST", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("SMART_FARM_BROKER_PORT", "1883"))
TEAM_ID = os.getenv("SMART_FARM_TEAM_ID", "team01")
CLIENT_ID = f"SmartFarm_Device_{os.uname().nodename}"

BASE_TOPIC = f"epg317e/farm/{TEAM_ID}"

# Control Topics
TOPICS = {
    "fan": f"{BASE_TOPIC}/fan",
    "pump": f"{BASE_TOPIC}/pump",
    "light": f"{BASE_TOPIC}/light",
    "temperature": f"{BASE_TOPIC}/temperature",
    "humidity": f"{BASE_TOPIC}/humidity",
}

# ================= GPIO CONFIGURATION (Raspberry Pi) =================
# If using Raspberry Pi with GPIO
try:
    import RPi.GPIO as GPIO
    USE_GPIO = True
    GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
    
    # GPIO pin assignments
    FAN_PIN = 17      # GPIO17
    PUMP_PIN = 27     # GPIO27
    LIGHT_PIN = 22    # GPIO22
    
    # Setup pins
    for pin in [FAN_PIN, PUMP_PIN, LIGHT_PIN]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    
except (ImportError, RuntimeError):
    print("⚠️ GPIO not available (not on Raspberry Pi). Running in simulation mode.")
    USE_GPIO = False

# ================= DEVICE STATE =================
device_state = {
    "fan": False,
    "pump": False,
    "light": False,
}

last_publish_time = {}

# ================= MQTT CALLBACKS =================

def on_connect(client, userdata, flags, rc):
    """Called when client connects to broker"""
    if rc == 0:
        print("✅ Connected to MQTT broker")
        
        # Subscribe to control topics
        for device, topic in TOPICS.items():
            client.subscribe(topic, qos=1)
        
        print(f"📡 Subscribed to {len(TOPICS)} topics")
        for device, topic in TOPICS.items():
            print(f"   - {topic}")
    else:
        print(f"❌ Connection failed with code {rc}")


def on_message(client, userdata, msg):
    """Called when message received"""
    topic = msg.topic
    payload = msg.payload.decode("utf-8", errors="replace").strip()
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 📨 {topic} → {payload}")
    
    # Determine if ON or OFF
    is_on = payload.upper() in ["ON", "1", "TRUE", "YES"]
    
    # Update state and GPIO
    if topic == TOPICS["fan"]:
        device_state["fan"] = is_on
        set_gpio(FAN_PIN, is_on)
        print(f"🌬 Fan: {'ON' if is_on else 'OFF'}")
    
    elif topic == TOPICS["pump"]:
        device_state["pump"] = is_on
        set_gpio(PUMP_PIN, is_on)
        print(f"💧 Pump: {'ON' if is_on else 'OFF'}")
    
    elif topic == TOPICS["light"]:
        device_state["light"] = is_on
        set_gpio(LIGHT_PIN, is_on)
        print(f"💡 Light: {'ON' if is_on else 'OFF'}")


def on_disconnect(client, userdata, rc):
    """Called when client disconnects"""
    if rc != 0:
        print(f"⚠️ Unexpected disconnection: {rc}")
    else:
        print("👋 Disconnected from MQTT broker")


# ================= GPIO CONTROL =================

def set_gpio(pin, state):
    """Set GPIO pin state"""
    if not USE_GPIO:
        print(f"[SIM] GPIO {pin}: {'HIGH' if state else 'LOW'}")
        return
    
    try:
        GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
    except Exception as e:
        print(f"❌ GPIO error: {e}")


def cleanup_gpio():
    """Clean up GPIO on exit"""
    if USE_GPIO:
        try:
            GPIO.cleanup()
            print("🧹 GPIO cleaned up")
        except Exception as e:
            print(f"⚠️ GPIO cleanup error: {e}")


# ================= SENSOR READING =================

def read_temperature():
    """Read temperature sensor (simulated or real)"""
    try:
        # For actual hardware, implement real sensor reading
        # Example: DHT22, DS18B20, etc.
        import random
        return 20 + random.uniform(-5, 5)
    except Exception as e:
        print(f"❌ Temperature read error: {e}")
        return None


def read_humidity():
    """Read humidity sensor (simulated or real)"""
    try:
        # For actual hardware, implement real sensor reading
        # Example: DHT22, etc.
        import random
        return 50 + random.uniform(-10, 10)
    except Exception as e:
        print(f"❌ Humidity read error: {e}")
        return None


# ================= PUBLISH SENSOR DATA =================

def publish_sensor_data(client):
    """Publish sensor readings to MQTT"""
    now = time.time()
    
    # Publish temperature
    if now - last_publish_time.get("temperature", 0) > 30:
        temp = read_temperature()
        if temp is not None:
            client.publish(TOPICS["temperature"], f"{temp:.1f}", qos=1)
            last_publish_time["temperature"] = now
    
    # Publish humidity
    if now - last_publish_time.get("humidity", 0) > 30:
        humidity = read_humidity()
        if humidity is not None:
            client.publish(TOPICS["humidity"], f"{humidity:.1f}", qos=1)
            last_publish_time["humidity"] = now


# ================= MAIN FUNCTION =================

def main():
    print("\n" + "=" * 60)
    print("🌱 Smart Farm - Hardware Device Controller")
    print("=" * 60)
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Team ID: {TEAM_ID}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"GPIO Mode: {'Enabled' if USE_GPIO else 'Simulation'}")
    print("=" * 60 + "\n")
    
    # Create MQTT client
    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Connect to broker
    print("🔄 Connecting to MQTT broker...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Start network loop
    client.loop_start()
    
    # Main loop
    try:
        print("✅ Device controller running (Press Ctrl+C to stop)\n")
        while True:
            # Publish sensor data periodically
            try:
                publish_sensor_data(client)
            except Exception as e:
                print(f"⚠️ Publish error: {e}")
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    
    finally:
        client.loop_stop()
        client.disconnect()
        cleanup_gpio()
        print("✅ Shutdown complete")


# ================= SIGNAL HANDLERS =================

def signal_handler(sig, frame):
    """Handle termination signals"""
    print("\n\n⚠️ Received signal, shutting down...")
    cleanup_gpio()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    main()
