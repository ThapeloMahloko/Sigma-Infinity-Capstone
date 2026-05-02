# Fixing the "Staircase" Effect in Sensor Data

## The Problem

Your original MQTT subscriber was creating a **new database row for each sensor message**. Since sensors publish independently to different topics (e.g., `TEMPERATURE`, `HUMIDITY`, `RAINFALL`), this resulted in:

- Row 1: `temperature=25.0, humidity=NULL, rainfall=NULL`
- Row 2: `temperature=NULL, humidity=60.0, rainfall=NULL`
- Row 3: `temperature=NULL, humidity=NULL, rainfall=5.2`

This created the "staircase" effect when visualizing the data, where each sensor's timeline shows as a step pattern rather than smooth values.

## The Solution

The new subscriber implements a **`SensorAggregator`** that:

1. **Collects measurements** from multiple MQTT topics into a temporary buffer
2. **Waits for a timeout** (5 seconds by default) or until minimum fields are received
3. **Flushes a complete row** with all available sensor data to the database

This results in complete readings like:
```
Row 1: timestamp=2026-05-02T10:15:00, temperature=25.0, humidity=60.0, rainfall=5.2, soil_moisture=45.0, ...
Row 2: timestamp=2026-05-02T10:15:05, temperature=25.1, humidity=59.8, rainfall=5.2, soil_moisture=44.9, ...
```

## Database Schema

The flat `SensorReading` model in `Database/Sql.py` stores all sensor values in **one row**:

```python
class SensorReading(Base):
    timestamp          → DateTime (indexed)
    temperature        → Float (nullable)
    humidity           → Float (nullable)
    soil_moisture      → Float (nullable)
    water_level        → Float (nullable)
    ambient_light      → Float (nullable)
    rainfall           → Float (nullable)
    motion_detection   → Float (nullable)
    ultrasonic_distance → Float (nullable)
    pump_status        → Float (nullable)
    fan_status         → Float (nullable)
```

## How to Use

### 1. Run the New Aggregating Subscriber

```bash
python subscriber/subscriber.py
```

The subscriber will:
- Connect to your MQTT broker at `localhost:1883`
- Subscribe to all sensor topics
- Collect measurements and flush them to the database every 5 seconds

### 2. Monitor the Database

```bash
python Database/Database.py
```

This shows the total readings and latest timestamp.

## MQTT Topic Mapping

The subscriber maps MQTT topics to database fields:

| MQTT Topic | Database Field | Type |
|-----------|----------------|------|
| `TEMPERATURE` | `temperature` | Float |
| `HUMIDITY` | `humidity` | Float |
| `SOIL_MOISTURE` | `soil_moisture` | Float |
| `WATER_LEVEL` | `water_level` | Float |
| `AMBIENT_LIGHT` | `ambient_light` | Float |
| `RAINFALL` | `rainfall` | Float |
| `MOTION_DETECTION` | `motion_detection` | Float |
| `ULTRASONIC_DISTANCE` | `ultrasonic_distance` | Float |
| `PUMP_STATUS` | `pump_status` | Float |
| `FAN_STATUS` | `fan_status` | Float |

To add new sensors, add them to the `topic_mapping` dictionary in `subscriber.py`.

## Configuration

### Aggregation Timeout

Change how long the aggregator waits before flushing data:

```python
aggregator = SensorAggregator(aggregation_timeout_seconds=10)  # Wait 10 seconds instead of 5
```

### MQTT Broker Address

Change the broker connection in `subscriber.py`:

```python
client.connect('192.168.1.100', 1883, keepalive=60)  # Connect to different IP
```

## Troubleshooting

### No data is being saved
- Check that your MQTT broker is running on `localhost:1883`
- Verify sensors are publishing to the correct topics
- Check the console output for error messages

### Missing fields in rows
- This is normal if not all sensors publish at the same frequency
- The 5-second timeout ensures readings are saved even if some sensors haven't reported

### Broker connection refused
- Start your MQTT broker (e.g., Mosquitto):
  ```bash
  mosquitto
  ```
- Or change the broker address in the subscriber code
