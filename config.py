# =========================================================
# CONFIGURATION
# =========================================================

import os

# MQTT CONFIG
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sitech/farm/#")

# DATABASE
DATABASE_URL = "sqlite:///smart_farm.db"

# TELEGRAM CONFIG
# Integrated Telegram bot token and chat id provided by the user
TELEGRAM_BOT_TOKEN = "8676954233:AAFyd_aFSAqWfq5UATmgL2zV_6UCEwX4Qm8"
TELEGRAM_CHAT_ID = "770459334"
# Leave username empty so the app will query getMe at runtime and resolve it
TELEGRAM_BOT_USERNAME = ""

# PANEL CONFIG
PANEL_PORT = 5006
PANEL_TITLE = "Smart Farm Dashboard"

# SENSOR CONFIG
SENSOR_TOPICS = {
    "sitech/farm/temp": "temperature",
    "sitech/farm/humidity": "humidity",
    "sitech/farm/soil": "soil",
    "sitech/farm/water": "water",
    "sitech/farm/light": "light",
    "sitech/farm/rain": "rain",
    "sitech/farm/fan_speed": "fan_speed",
}

SENSOR_LABELS = {
    "temperature": "Temperature",
    "humidity": "Humidity",
    "soil": "Soil Moisture",
    "water": "Water Level",
    "light": "Light",
    "rain": "Rain",
    "fan_speed": "Fan Speed",
}

SENSOR_UNITS = {
    "temperature": "°C",
    "humidity": "%",
    "soil": "%",
    "water": "%",
    "light": "%",
    "rain": "%",
    "fan_speed": "",
}

# UI CONFIG
MAX_POINTS = 50
ANALYTICS_MAX_ROWS = 1000
EXPORT_PREVIEW_ROWS = 1000

# COLORS
COLOR_PRIMARY = "#0e1b27"
COLOR_SECONDARY = "#112334"
COLOR_ACCENT = "#4fd1a5"
COLOR_ACCENT_LIGHT = "#92e6c7"
COLOR_TEXT = "#f4f8fb"
COLOR_TEXT_MUTED = "#9bb5c5"
COLOR_BORDER = "#20374a"
COLOR_BACKGROUND = "#07111a"
