/*
===========================================================
SMART FARM HARDWARE CODE
LIVE DASHBOARD VERSION
===========================================================

FEATURES
✔ Real-time MQTT sensor publishing
✔ Temperature
✔ Humidity
✔ Soil Moisture
✔ Water Level
✔ Rain Sensor
✔ Light Sensor
✔ PIR Motion Sensor
✔ Fan PWM Control
✔ Pump Control
✔ Alarm System
✔ Feeder Servo
✔ Telegram-ready alerts
✔ Dashboard-ready topics

===========================================================
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <DHT11.h>
#include <ESP32Servo.h>

// ===========================================================
// WIFI CONFIG
// ===========================================================

const char* ssid = "TP";
const char* password = "Th@pelo0127";

// ===========================================================
// MQTT
// ===========================================================

const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

// ===========================================================
// LCD
// ===========================================================

LiquidCrystal_I2C lcd(0x27, 16, 2);

// ===========================================================
// SENSOR PINS
// ===========================================================

#define DHT11PIN 17

#define SOILPIN 32
#define WATERPIN 33
#define LIGHTPIN 34
#define RAINPIN 35

#define PIRPIN 23

// ===========================================================
// ACTUATOR PINS
// ===========================================================

#define FANPIN1 19
#define FANPIN2 18

#define PUMPPIN 25

#define BUZZERPIN 16

#define LEDPIN 27

// ===========================================================
// SERVO + ULTRASONIC
// ===========================================================

#define TrigPin 12
#define EchoPin 13
#define ServoPin 26

Servo feederServo;

// ===========================================================
// OBJECTS
// ===========================================================

DHT11 dht11(DHT11PIN);

// ===========================================================
// VARIABLES
// ===========================================================

int fanSpeed = 0;

bool manualMode = false;

bool alarmArmed = false;

bool pirTriggered = false;

int currentServoPos = 100;

bool feederOpen = false;

// ===========================================================
// WIFI SETUP
// ===========================================================

void setup_wifi() {

  Serial.println();
  Serial.println("CONNECTING TO WIFI");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);

    Serial.print(".");
  }

  Serial.println();
  Serial.println("WIFI CONNECTED");

  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// ===========================================================
// EMERGENCY SIREN
// ===========================================================

void emergencySiren() {

  for (int i = 200; i <= 1000; i += 20) {

    tone(BUZZERPIN, i);

    delay(5);
  }

  for (int i = 1000; i >= 200; i -= 20) {

    tone(BUZZERPIN, i);

    delay(5);
  }
}

// ===========================================================
// SERVO FUNCTION
// ===========================================================

void moveServoSmooth(int startPos, int endPos) {

  if (startPos < endPos) {

    for (int pos = startPos; pos <= endPos; pos++) {

      feederServo.write(pos);

      delay(10);
    }
  }

  else {

    for (int pos = startPos; pos >= endPos; pos--) {

      feederServo.write(pos);

      delay(10);
    }
  }

  currentServoPos = endPos;
}

// ===========================================================
// DISTANCE FUNCTION
// ===========================================================

float getDistance() {

  digitalWrite(TrigPin, LOW);

  delayMicroseconds(2);

  digitalWrite(TrigPin, HIGH);

  delayMicroseconds(10);

  digitalWrite(TrigPin, LOW);

  int duration = pulseIn(EchoPin, HIGH);

  int distance = duration / 58;

  return distance;
}

// ===========================================================
// MQTT CALLBACK
// ===========================================================

void callback(char* topic, byte* payload, unsigned int length) {

  String msg = "";

  for (int i = 0; i < length; i++) {

    msg += (char)payload[i];
  }

  Serial.println();
  Serial.println("========== MQTT ==========");

  Serial.print("TOPIC: ");
  Serial.println(topic);

  Serial.print("MESSAGE: ");
  Serial.println(msg);

  // =========================================================
  // FAN SPEED
  // =========================================================

  if (String(topic) == "sitech/farm/control/fan_speed") {

    fanSpeed = msg.toInt();

    manualMode = true;

    Serial.print("FAN SPEED: ");
    Serial.println(fanSpeed);
  }

  // =========================================================
  // FAN MODE
  // =========================================================

  if (String(topic) == "sitech/farm/control/mode") {

    if (msg == "AUTO") {

      manualMode = false;

      Serial.println("AUTO MODE");
    }

    if (msg == "MANUAL") {

      manualMode = true;

      Serial.println("MANUAL MODE");
    }
  }

  // =========================================================
  // PUMP CONTROL
  // =========================================================

  if (String(topic) == "sitech/farm/control/pump") {

    if (msg == "ON") {

      digitalWrite(PUMPPIN, HIGH);

      Serial.println("PUMP ON");
    }

    else {

      digitalWrite(PUMPPIN, LOW);

      Serial.println("PUMP OFF");
    }
  }

  // =========================================================
  // ALARM CONTROL
  // =========================================================

  if (String(topic) == "sitech/farm/control/alarm") {

    if (msg == "ON") {

      alarmArmed = true;

      pirTriggered = false;

      Serial.println("ALARM ARMED");

      client.publish(
        "sitech/farm/alarm_status",
        "ARMED"
      );
    }

    else {

      alarmArmed = false;

      pirTriggered = false;

      noTone(BUZZERPIN);

      digitalWrite(LEDPIN, LOW);

      Serial.println("ALARM DISARMED");

      client.publish(
        "sitech/farm/alarm_status",
        "DISARMED"
      );
    }
  }

  // =========================================================
  // FEEDER CONTROL
  // =========================================================

  if (String(topic) == "sitech/farm/control/feed") {

    if (msg == "OPEN") {

      Serial.println("OPEN FEEDER");

      moveServoSmooth(currentServoPos, 0);

      feederOpen = true;

      client.publish(
        "sitech/farm/feed_status",
        "OPEN"
      );
    }

    if (msg == "CLOSE") {

      Serial.println("CLOSE FEEDER");

      moveServoSmooth(currentServoPos, 100);

      feederOpen = false;

      client.publish(
        "sitech/farm/feed_status",
        "CLOSED"
      );
    }
  }
}

// ===========================================================
// MQTT RECONNECT
// ===========================================================

void reconnect() {

  while (!client.connected()) {

    Serial.println("CONNECTING MQTT...");

    if (client.connect("ESP32SmartFarm")) {

      Serial.println("MQTT CONNECTED");

      client.subscribe("sitech/farm/control/#");

      Serial.println("SUBSCRIBED");
    }

    else {

      Serial.println("MQTT FAILED");

      delay(3000);
    }
  }
}

// ===========================================================
// SETUP
// ===========================================================

void setup() {

  Serial.begin(115200);

  Serial.println();
  Serial.println("SMART FARM STARTING");

  // LCD
  Wire.begin(21, 22);

  lcd.init();

  lcd.backlight();

  lcd.clear();

  lcd.setCursor(0, 0);

  lcd.print("SMART FARM");

  lcd.setCursor(0, 1);

  lcd.print("BOOTING");

  // PINS
  pinMode(FANPIN1, OUTPUT);
  pinMode(FANPIN2, OUTPUT);

  pinMode(PUMPPIN, OUTPUT);

  pinMode(BUZZERPIN, OUTPUT);

  pinMode(LEDPIN, OUTPUT);

  pinMode(PIRPIN, INPUT);

  pinMode(TrigPin, OUTPUT);

  pinMode(EchoPin, INPUT);

  // SERVO
  feederServo.attach(ServoPin);

  feederServo.write(100);

  currentServoPos = 100;

  // WIFI
  setup_wifi();

  // MQTT
  client.setServer(mqtt_server, 1883);

  client.setCallback(callback);

  Serial.println("SYSTEM READY");
}

// ===========================================================
// LOOP
// ===========================================================

void loop() {

  if (!client.connected()) {

    reconnect();
  }

  client.loop();

  // =========================================================
  // DHT11
  // =========================================================

  int temp = 0;
  int humidity = 0;

  int result = dht11.readTemperatureHumidity(
    temp,
    humidity
  );

  if (result != 0) {

    Serial.println("DHT11 ERROR");

    delay(2000);

    return;
  }

  // =========================================================
  // ANALOG SENSORS
  // =========================================================

  int soilRaw = analogRead(SOILPIN);

  int waterRaw = analogRead(WATERPIN);

  int lightRaw = analogRead(LIGHTPIN);

  int rainRaw = analogRead(RAINPIN);

  // =========================================================
  // CONVERT TO %
  // =========================================================

  float soil = map(soilRaw, 4095, 0, 0, 100);

  float water = map(waterRaw, 0, 4095, 0, 100);

  float rain = map(rainRaw, 4095, 0, 0, 100);

  float light = map(lightRaw, 0, 4095, 0, 100);

  // =========================================================
  // DISTANCE
  // =========================================================

  float distance = getDistance();

  // =========================================================
  // AUTO FEEDING
  // =========================================================

  if (distance >= 2 && distance <= 7) {

    if (!feederOpen) {

      Serial.println("AUTO FEED");

      moveServoSmooth(currentServoPos, 0);

      feederOpen = true;

      delay(3000);

      moveServoSmooth(currentServoPos, 100);

      feederOpen = false;
    }
  }

  // =========================================================
  // PIR SENSOR
  // =========================================================

  bool motionDetected = digitalRead(PIRPIN);

  if (alarmArmed) {

    if (motionDetected && !pirTriggered) {

      pirTriggered = true;

      Serial.println("MOTION DETECTED");

      digitalWrite(LEDPIN, HIGH);

      emergencySiren();

      client.publish(
        "sitech/farm/alert",
        "MOTION"
      );
    }

    if (!motionDetected) {

      pirTriggered = false;

      noTone(BUZZERPIN);

      digitalWrite(LEDPIN, LOW);
    }
  }

  else {

    pirTriggered = false;

    noTone(BUZZERPIN);

    digitalWrite(LEDPIN, LOW);
  }

  // =========================================================
  // AUTO FAN
  // =========================================================

  if (!manualMode) {

    if (temp >= 29) {

      fanSpeed = 150;
    }

    else {

      fanSpeed = 0;
    }
  }

  analogWrite(FANPIN1, fanSpeed);

  analogWrite(FANPIN2, 0);

  // =========================================================
  // LCD
  // =========================================================

  lcd.clear();

  lcd.setCursor(0, 0);

  lcd.print("T:");
  lcd.print(temp);

  lcd.print(" H:");
  lcd.print(humidity);

  lcd.setCursor(0, 1);

  lcd.print("S:");
  lcd.print((int)soil);

  lcd.print("%");

  // =========================================================
  // SERIAL DEBUG
  // =========================================================

  Serial.println();
  Serial.println("========== LIVE DATA ==========");

  Serial.print("TEMP: ");
  Serial.println(temp);

  Serial.print("HUMIDITY: ");
  Serial.println(humidity);

  Serial.print("SOIL: ");
  Serial.println(soil);

  Serial.print("WATER: ");
  Serial.println(water);

  Serial.print("LIGHT: ");
  Serial.println(light);

  Serial.print("RAIN: ");
  Serial.println(rain);

  Serial.print("FAN SPEED: ");
  Serial.println(fanSpeed);

  // =========================================================
  // MQTT PUBLISH
  // =========================================================

  client.publish(
    "sitech/farm/temp",
    String(temp).c_str()
  );

  client.publish(
    "sitech/farm/humidity",
    String(humidity).c_str()
  );

  client.publish(
    "sitech/farm/soil",
    String(soil).c_str()
  );

  client.publish(
    "sitech/farm/water",
    String(water).c_str()
  );

  client.publish(
    "sitech/farm/light",
    String(light).c_str()
  );

  client.publish(
    "sitech/farm/rain",
    String(rain).c_str()
  );

  client.publish(
    "sitech/farm/fan_speed",
    String(fanSpeed).c_str()
  );

  delay(2000);
}