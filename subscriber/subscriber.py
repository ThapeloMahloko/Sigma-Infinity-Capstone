import paho.mqtt.client as mqtt
import time

def on_message(client, userdata, message):
    print("Received message on topic '" + message.topic + "': " 
          + str(message.payload.decode("utf-8")))

mqttBroker = "broker.hivemq.com"
client = None

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "SmartFarm_Receiver")
    client.connect(mqttBroker, port=1883, keepalive=60)
    client.loop_start()
    
    # Subscribe to all ESP32 publisher topics
    client.subscribe("TEMPERATURE")
    client.subscribe("HUMIDITY")
    client.subscribe("SOIL_MOISTURE")
    client.subscribe("LIGHT_LEVEL")
    client.subscribe("WATER_LEVEL")
    client.subscribe("RAIN_VALUE")
    
    client.on_message = on_message
    
    print("Connected to broker and subscribed to ESP32 Smart Farm publisher topics.")
    print("Waiting for sensor data...\n")
    
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nSubscriber stopped.")
    if client is not None:
        client.loop_stop()
        client.disconnect()
except Exception as e:
    print(f"An error occurred: {e}")