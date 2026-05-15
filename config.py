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
# Read Telegram credentials from environment variables so they can be
# supplied securely via Hugging Face Space Secrets or process env.
# Example (in Space UI -> Settings -> Secrets):
# TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# Leave username empty so the app will query getMe at runtime and resolve it
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")

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

# COLORS - DARK MODE (DEFAULT)
COLOR_PRIMARY = "#0c1f1a"
COLOR_SECONDARY = "#0b1f1a"
COLOR_ACCENT = "#42d392"
COLOR_ACCENT_LIGHT = "#7fe8b8"
COLOR_TEXT = "#ffffff"
COLOR_TEXT_MUTED = "#8fb8aa"
COLOR_BORDER = "#16352d"
COLOR_BACKGROUND = "#071411"

# COLORS - LIGHT MODE
COLOR_PRIMARY_LIGHT = "#eaf2ef"
COLOR_SECONDARY_LIGHT = "#e0ece8"
COLOR_ACCENT_LIGHT_MODE = "#1a6b52"
COLOR_ACCENT_LIGHT_MODE_LIGHT = "#4a7a6a"
COLOR_TEXT_LIGHT = "#0d2015"
COLOR_TEXT_MUTED_LIGHT = "#7aaa98"
COLOR_BORDER_LIGHT = "#b8d4cc"
COLOR_BACKGROUND_LIGHT = "#f0f5f3"
