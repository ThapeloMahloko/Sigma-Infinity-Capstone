import paho.mqtt.client as mqtt
import Sql
from Sql import SensorReading
from datetime import datetime
import time

def on_message(client, userdata, message):
    print("Received message on topic '" + message.topic + "': "
          + str(message.payload.decode("utf-8")))
    humidity = 0.0
    water_level = 0.0
    ambient_light = 0.0
    rainfall = 0.0
    soil_moisture = 0.0
    temperature = 0.0
    session = Sql.Session()

    if message.topic == "TEMPERATURE":
        temperature = float(message.payload.decode("utf-8"))
    if message.topic == "HUMIDITY":
        humidity = float(message.payload.decode("utf-8"))
    if message.topic == "SOIL_MOISTURE":
        soil_moisture = float(message.payload.decode("utf-8"))
    if message.topic == "LIGHT_LEVEL":
        ambient_light = float(message.payload.decode("utf-8"))
    if message.topic == "WATER_LEVEL":
        water_level = float(message.payload.decode("utf-8"))
    if message.topic == "RAIN_VALUE":
        rainfall = float(message.payload.decode("utf-8"))       

    # Add more topics as needed
    Data = SensorReading(
        temperature=temperature,
        humidity=humidity,
        ambient_light=ambient_light,
        soil_moisture=soil_moisture,
        water_level=water_level,
        rainfall=rainfall)
    session.add(Data)
    session.commit()
    print(str(datetime.now()))
    last_entry = session.query(SensorReading).order_by(SensorReading.id.desc()).first()
    print(f"Latest entry in database: {last_entry}")

mqttBroker = "broker.hivemq.com"
client = "ESP32_SmartFarm_Receiver"

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Smartphone")
    client.connect(mqttBroker, port=1883, keepalive=60)

    client.subscribe("TEMPERATURE")
    client.subscribe("HUMIDITY")
    client.subscribe("SOIL_MOISTURE")
    client.subscribe("LIGHT_LEVEL")
    client.subscribe("WATER_LEVEL")
    client.subscribe("RAIN_VALUE")

    client.on_message = on_message

    # ⏱️ Run subscriber for 30 seconds only, then stop
    client.loop_start()
    time.sleep(30)
    client.loop_stop()

except ConnectionRefusedError:
    print("Connection refused. Check broker address and network.")
except KeyboardInterrupt:
    print("Subscriber stopped.")
    if client is not None:
        client.loop_stop()
        client.disconnect()
except Exception as e:
    print(f"An error occurred: {e}")