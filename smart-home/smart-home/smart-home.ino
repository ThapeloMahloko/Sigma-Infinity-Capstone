#include <SimpleDHT.h>

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <SimpleDHT.h>
#include <ESP32Servo.h>
#include <LiquidCrystal_I2C.h>

// ================= SENSOR PINS =================
#define DHT11PIN 17         // Air Temp & Humidity
#define RAINPIN 35          // Rain sensor
#define LIGHTPIN 34         // Sunlight sensor
#define WATERLEVELPIN 33    // Tank level
#define SOILPIN 32          // Soil moisture

// ================= ACTUATORS =================
#define LEDPIN 27           // Farm light indicator
#define PUMPPIN 25          // Water pump relay
#define SERVOPIN 26         // Feed dispenser
#define FANPIN1 19          // Ventilation fan +
#define FANPIN2 18          // Ventilation fan -
#define BUZZERPIN 16        // Alarm

// ================= WIFI & MQTT =================
const char* ssid = "TP";
const char* pwd  = "Th@pelo0127";

const char* MQTT_BROKER   = "broker.hivemq.com";
const uint16_t MQTT_PORT  = 1883;
const char* MQTT_CLIENT_ID = "ESP32_SmartFarm_Kabo";

// ================= TIMING =================
const uint32_t PUBLISH_INTERVAL_MS = 2000;  // Publish every 2 seconds
const uint32_t SENSOR_READ_INTERVAL_MS = 2000;  // Read sensors every 2 seconds
uint32_t lastPublishMs = 0;
uint32_t lastSensorReadMs = 0;

// ================= OBJECTS =================
LiquidCrystal_I2C lcd(0x27, 16, 2);
WiFiServer server(80);
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
SimpleDHT11 dht11(DHT11PIN);
Servo feederServo;

// ================= VARIABLES =================
String request;
String dataBuffer;

int temperature;
int humidity;
int soilMoisture;
int lightLevel;
int waterLevel;
int rainValue;

// ================= SETUP =================
void connectMQTT() {
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  
  while (!mqtt.connected()) {
    Serial.printf("Connecting to MQTT broker %s ... ", MQTT_BROKER);
    if (mqtt.connect(MQTT_CLIENT_ID)) {
      Serial.println("connected");
    } else {
      Serial.printf("failed (rc=%d), retrying in 2 s\n", mqtt.state());
      delay(2000);
    }
  }
}

void publishFloat(const char* topic, float value, uint8_t decimals = 2) {
  char buf[16];
  dtostrf(value, 0, decimals, buf);
  mqtt.publish(topic, buf);
  Serial.printf("Published %s -> %s\n", topic, buf);
}

void setup() {
  Serial.begin(115200);

  // WiFi connection
  WiFi.begin(ssid, pwd);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.println(WiFi.localIP());

  // LCD Setup
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Smart Farm");
  lcd.setCursor(0, 1);
  lcd.print("Initializing...");

  // Pin modes
  pinMode(LEDPIN, OUTPUT);
  pinMode(PUMPPIN, OUTPUT);
  pinMode(FANPIN1, OUTPUT);
  pinMode(FANPIN2, OUTPUT);
  pinMode(BUZZERPIN, OUTPUT);

  pinMode(RAINPIN, INPUT);
  pinMode(LIGHTPIN, INPUT);
  pinMode(SOILPIN, INPUT);
  pinMode(WATERLEVELPIN, INPUT);

  feederServo.attach(SERVOPIN);
  feederServo.write(160); // Closed

  server.begin();

  // Buzzer PWM
  ledcAttachChannel(BUZZERPIN, 1000, 8, 4);
  
  // MQTT connection
  connectMQTT();
}

// ================= MAIN LOOP =================
void loop() {
  // Keep MQTT connection alive
  if (!mqtt.connected()) {
    connectMQTT();
  }
  mqtt.loop();

  uint32_t now = millis();
  
  // Read sensors at slower interval
  if (now - lastSensorReadMs >= SENSOR_READ_INTERVAL_MS) {
    lastSensorReadMs = now;
    getSensorData();
    
    // Update LCD with temperature and humidity
    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print(temperature);
    lcd.print("C H:");
    lcd.print(humidity);
    lcd.print("%");
    lcd.setCursor(0, 1);
    lcd.print("WiFi:");
    if (WiFi.status() == WL_CONNECTED) {
      lcd.print("OK");
    } else {
      lcd.print("NO");
    }
    lcd.print(" MQTT:");
    if (mqtt.connected()) {
      lcd.print("OK");
    } else {
      lcd.print("NO");
    }
  }
  
  // Publish sensor data at slower interval
  if (now - lastPublishMs >= PUBLISH_INTERVAL_MS) {
    lastPublishMs = now;
    
    publishFloat("TEMPERATURE", (float)temperature, 2);
    publishFloat("HUMIDITY", (float)humidity, 2);
    publishFloat("SOIL_MOISTURE", (float)(soilMoisture / 10.0), 1);
    publishFloat("LIGHT_LEVEL", (float)(lightLevel / 10.0), 1);
    publishFloat("WATER_LEVEL", (float)(waterLevel / 10.0), 1);
    publishFloat("RAIN_VALUE", (float)(rainValue / 10.0), 1);
  }

  // WiFi server handling (existing functionality)
  WiFiClient client = server.available();

  if (client) {
    Serial.println("Client connected");

    while (client.connected()) {

      if (client.available()) {
        request = client.readStringUntil('s');
        Serial.println(request);
      }

      getSensorData();

      // Send data
      dataBuffer = "";
      dataBuffer += String(temperature, HEX);
      dataBuffer += String(humidity, HEX);
      dataBuffer += toHexPercent(soilMoisture);
      dataBuffer += toHexPercent(lightLevel);
      dataBuffer += toHexPercent(waterLevel);
      dataBuffer += toHexPercent(rainValue);

      client.print(dataBuffer);

      // ================= AUTOMATION =================

      // 🌱 Irrigation control
      if (soilMoisture < 40 && waterLevel > 20) {
        digitalWrite(PUMPPIN, HIGH); // Start watering
      } else {
        digitalWrite(PUMPPIN, LOW);
      }

      // 🌡 Temperature control
      if (temperature > 30) {
        digitalWrite(FANPIN1, HIGH);
        digitalWrite(FANPIN2, LOW);
      } else {
        digitalWrite(FANPIN1, LOW);
        digitalWrite(FANPIN2, LOW);
      }

      // 🌧 Rain alert
      if (rainValue > 80) {
        ledcWriteTone(BUZZERPIN, 400);
      } else {
        ledcWriteTone(BUZZERPIN, 0);
      }

      // 💡 Light indicator (night detection)
      if (lightLevel < 20) {
        digitalWrite(LEDPIN, HIGH);
      } else {
        digitalWrite(LEDPIN, LOW);
      }

      // ================= MANUAL COMMANDS =================
      if (request == "f") {         // Feed animals
        feederServo.write(80);
        delay(500);
        feederServo.write(160);
      }

      request = "";
      delay(100);
    }

    client.stop();
    Serial.println("Client disconnected");
  }
}

// ================= SENSOR FUNCTION =================
void getSensorData() {
  byte temp, hum;
  if (dht11.read(&temp, &hum, NULL) == SimpleDHTErrSuccess) {
    temperature = temp;
    humidity = hum;
  }

  rainValue    = analogRead(RAINPIN);
  lightLevel   = analogRead(LIGHTPIN);
  soilMoisture = analogRead(SOILPIN) * 1.8;
  waterLevel   = analogRead(WATERLEVELPIN) * 1.8;
}

// ================= HELPER FUNCTION =================
String toHexPercent(int data) {
  int percentage = (data / 4095.0) * 100;
  percentage = percentage > 100 ? 100 : percentage;

  char hexString[3];
  sprintf(hexString, "%02X", percentage);
  return hexString;
}