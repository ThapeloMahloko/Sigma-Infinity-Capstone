import paho.mqtt.client as mqtt
import time
from datetime import datetime

# Buffer to store sensor data
sensor_data = {
    "TEMPERATURE": None,
    "HUMIDITY": None,
    "SOIL_MOISTURE": None,
    "LIGHT_LEVEL": None,
    "WATER_LEVEL": None,
    "RAIN_VALUE": None
}

received_topics = set()
batch_complete = False
ready_for_new_batch = True

def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected successfully")
        client.subscribe("TEMPERATURE", qos=1)
        client.subscribe("HUMIDITY", qos=1)
        client.subscribe("SOIL_MOISTURE", qos=1)
        client.subscribe("LIGHT_LEVEL", qos=1)
        client.subscribe("WATER_LEVEL", qos=1)
        client.subscribe("RAIN_VALUE", qos=1)

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Disconnected: {reason_code}")

def on_message(client, userdata, message):
    global received_topics, batch_complete, ready_for_new_batch
    
    # Only collect messages if ready for a new batch
    if not ready_for_new_batch:
        return
    
    topic = message.topic
    payload = str(message.payload.decode("utf-8"))
    
    if topic in sensor_data:
        sensor_data[topic] = payload
        received_topics.add(topic)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {topic}: {payload}")
        
        # Check if all 6 sensors have been received
        if len(received_topics) == 6:
            batch_complete = True
            ready_for_new_batch = False
            publish_to_database()

def publish_to_database():
    global received_topics, ready_for_new_batch
    
    print("\n" + "="*60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ COMPLETE DATA - READY FOR DATABASE")
    print("="*60)
    print(f"TEMPERATURE:   {sensor_data['TEMPERATURE']}°C")
    print(f"HUMIDITY:      {sensor_data['HUMIDITY']}%")
    print(f"SOIL_MOISTURE: {sensor_data['SOIL_MOISTURE']}%")
    print(f"LIGHT_LEVEL:   {sensor_data['LIGHT_LEVEL']}%")
    print(f"WATER_LEVEL:   {sensor_data['WATER_LEVEL']}%")
    print(f"RAIN_VALUE:    {sensor_data['RAIN_VALUE']}%")
    print("="*60)
    print("Waiting 5 seconds before accepting next batch...\n")
    
    # Wait 5 seconds before accepting next batch
    time.sleep(5)
    
    # Reset for next batch
    received_topics.clear()
    ready_for_new_batch = True
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ready for next batch\n")

mqttBroker = "broker.hivemq.com"
client = None

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "SmartFarm_Receiver")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect(mqttBroker, port=1883, keepalive=60)
    client.loop_start()
    
    print("Connecting to broker...")
    print("Waiting for complete sensor dataset...\n")
    
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nSubscriber stopped.")
    if client is not None:
        client.loop_stop()
        client.disconnect()
except Exception as e:
    print(f"An error occurred: {e}")