"""
MQTT Subscriber for Smart Farm Sensor Data with Aggregation.

This subscriber collects sensor readings from multiple MQTT topics and aggregates
them into complete sensor readings before writing to the database. This prevents
the "staircase" effect caused by recording each sensor event as a separate row.
"""

import json
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from threading import Lock
import sys
from pathlib import Path

# Add parent directory to path for database imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Database.Sql import SensorReading, SessionLocal, init_db, DATABASE_PATH


class SensorAggregator:
    """Aggregates sensor readings from multiple MQTT topics into complete readings."""
    
    def __init__(self, aggregation_timeout_seconds=5):
        """
        Initialize the aggregator.
        
        Args:
            aggregation_timeout_seconds: How long to wait before flushing partial data (seconds)
        """
        self.aggregation_timeout_seconds = aggregation_timeout_seconds
        self.current_reading = {}
        self.last_update_time = datetime.utcnow()
        self.lock = Lock()
        self.session = SessionLocal()
        
    def add_measurement(self, topic, value):
        """
        Add a measurement from an MQTT topic.
        
        Maps MQTT topic names to sensor fields and automatically flushes
        complete readings to the database.
        """
        with self.lock:
            # Map MQTT topics to SensorReading fields
            topic_mapping = {
                'TEMPERATURE': 'temperature',
                'HUMIDITY': 'humidity',
                'SOIL_MOISTURE': 'soil_moisture',
                'WATER_LEVEL': 'water_level',
                'AMBIENT_LIGHT': 'ambient_light',
                'RAINFALL': 'rainfall',
                'MOTION_DETECTION': 'motion_detection',
                'ULTRASONIC_DISTANCE': 'ultrasonic_distance',
                'PUMP_STATUS': 'pump_status',
                'FAN_STATUS': 'fan_status',
            }
            
            # Convert topic to field name
            field_name = topic_mapping.get(topic)
            if field_name is None:
                print(f"⚠️  Unknown topic: {topic}")
                return
            
            # Initialize reading dict if empty
            if not self.current_reading:
                self.current_reading['timestamp'] = datetime.utcnow()
            
            # Add/update the measurement
            try:
                self.current_reading[field_name] = float(value)
                print(f"✓ {field_name}: {value}")
            except ValueError:
                print(f"⚠️  Invalid value for {field_name}: {value}")
                return
            
            # Check if we should flush (either timeout or enough fields collected)
            time_since_start = datetime.utcnow() - self.current_reading['timestamp']
            min_fields = 3  # At minimum, require 3 sensor fields
            
            if (time_since_start.total_seconds() > self.aggregation_timeout_seconds or 
                len([v for v in self.current_reading.values() if v is not None]) >= min_fields):
                self._flush_reading()
    
    def _flush_reading(self):
        """Write the current aggregated reading to the database."""
        if not self.current_reading or len(self.current_reading) <= 1:
            return
        
        try:
            reading = SensorReading(**self.current_reading)
            self.session.add(reading)
            self.session.commit()
            
            # Print the saved reading
            sensor_values = {k: v for k, v in self.current_reading.items() if k != 'timestamp' and v is not None}
            print(f"\n📊 Saved reading: {sensor_values}\n")
            
            # Reset for next reading
            self.current_reading = {}
        except Exception as e:
            print(f"❌ Error saving reading: {e}")
            self.session.rollback()


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    """Called when connected to MQTT broker."""
    if rc == 0:
        print("✓ Connected to broker")
        # Subscribe to all sensor topics
        topics = [
            'TEMPERATURE',
            'HUMIDITY',
            'SOIL_MOISTURE',
            'WATER_LEVEL',
            'AMBIENT_LIGHT',
            'RAINFALL',
            'MOTION_DETECTION',
            'ULTRASONIC_DISTANCE',
            'PUMP_STATUS',
            'FAN_STATUS',
        ]
        for topic in topics:
            client.subscribe(topic)
            print(f"  Subscribed to: {topic}")
    else:
        print(f"❌ Connection failed with code {rc}")


def on_message(client, userdata, msg):
    """Called when a message is received from the broker."""
    aggregator = userdata
    try:
        # Decode payload
        payload = msg.payload.decode('utf-8').strip()
        topic = msg.topic
        
        # Handle JSON payload (common in IoT)
        try:
            data = json.loads(payload)
            if isinstance(data, dict) and 'value' in data:
                value = data['value']
            else:
                value = payload
        except json.JSONDecodeError:
            value = payload
        
        # Add to aggregator
        aggregator.add_measurement(topic, value)
    except Exception as e:
        print(f"❌ Error processing message on {msg.topic}: {e}")


def on_disconnect(client, userdata, rc):
    """Called when disconnected from MQTT broker."""
    if rc != 0:
        print(f"⚠️  Unexpected disconnection (code {rc})")


def main():
    """Main entry point for the MQTT subscriber."""
    # Initialize database
    init_db()
    print(f"📁 Database: {DATABASE_PATH}")
    print("Starting MQTT subscriber with sensor aggregation...\n")
    
    # Create aggregator
    aggregator = SensorAggregator(aggregation_timeout_seconds=5)
    
    # Setup MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=aggregator)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to broker
        client.connect('localhost', 1883, keepalive=60)
        
        # Start network loop
        print("Waiting for sensor data...\n")
        client.loop_forever()
    except ConnectionRefusedError:
        print("❌ Could not connect to MQTT broker at localhost:1883")
        print("   Make sure your MQTT broker (e.g., Mosquitto) is running")
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        client.disconnect()
        client.loop_stop()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        aggregator.session.close()


if __name__ == "__main__":
    main()
