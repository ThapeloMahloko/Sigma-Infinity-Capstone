# QUICK START GUIDE

## Project Overview

The Smart Farm Dashboard has been refactored from a single monolithic script into a modular, well-organized project structure.

### Old Structure
```
exe.py (1700+ lines)
```

### New Structure
```
smart_farm_dashboard/
├── main.py                 # Run this to start
├── config.py               # All settings
├── database.py             # DB models
├── mqtt_handler.py         # MQTT logic
├── ui_components.py        # Shared UI
├── utils.py                # Helpers
├── pages/
│   ├── dashboard.py
│   ├── analytics.py
│   ├── export.py
│   ├── controls.py
│   └── telegram.py
└── requirements.txt
```

## Installation & Running

### Step 1: Navigate to the project
```bash
cd "c:\Users\thaba\OneDrive\Documents\Test Farm\smart_farm_dashboard"
```

### Step 2: Install dependencies (first time only)
```bash
pip install -r requirements.txt
```

### Step 3: Run the dashboard
```bash
python main.py
```

### Step 4: Open browser
- Automatically opens `http://localhost:5006`
- Or manually navigate there

## File Organization Benefits

| Aspect | Before | After |
|--------|--------|-------|
| Lines of Code | 1700+ in one file | ~200-300 per module |
| Finding Code | Hard to locate | Clear location for each feature |
| Adding Features | Risk of breaking things | Add new page easily |
| Testing | Difficult | Can test modules independently |
| Reusability | Limited | Import utils/components anywhere |
| Maintenance | Time-consuming | Quick edits in focused files |

## Key Files to Know

- **main.py** - Start here. Imports everything and runs the server.
- **config.py** - Change MQTT broker, sensors, colors, ports here.
- **pages/dashboard.py** - Edit live dashboard layout.
- **pages/analytics.py** - Modify filters, stats, plots.
- **pages/export.py** - Add new export formats here.
- **utils.py** - Helper functions used across pages.

## Common Tasks

### Change MQTT Broker
Edit `config.py`:
```python
MQTT_BROKER = "your.broker.com"
MQTT_PORT = 1883
```

### Add New Sensor
Edit `config.py`:
```python
SENSOR_TOPICS = {
    "sitech/farm/temp": "temperature",
    "sitech/farm/new_sensor": "new_sensor",  # Add this
}

SENSOR_LABELS = {
    "temperature": "Temperature",
    "new_sensor": "My New Sensor",  # Add this
}

SENSOR_UNITS = {
    "temperature": "°C",
    "new_sensor": "%",  # Add this
}
```

It will automatically appear in all dropdowns and pages.

### Add New Page
1. Create `pages/new_page.py`
2. Define `new_page` variable
3. Import in `main.py`:
   ```python
   from pages.new_page import new_page
   ```
4. Add button in sidebar:
   ```python
   new_page_btn = pn.widgets.Button(name="📄 New Page")
   new_page_btn.on_click(lambda e: show_new_page())
   sidebar.append(new_page_btn)
   ```

### Customize Colors
Edit `config.py`:
```python
COLOR_PRIMARY = "#0c1f1a"        # Main background
COLOR_ACCENT = "#42d392"         # Highlights
COLOR_TEXT = "#ffffff"           # Text color
```

## Architecture Overview

```
User Browser
    ↓
main.py (Flask/Panel Server)
    ├── MQTT Handler → ESP32/Sensors
    ├── Database ← Historical Data
    └── UI Pages
        ├── Dashboard (Live)
        ├── Analytics (Filtered)
        ├── Export (Download)
        ├── Controls (MQTT Send)
        └── Telegram (Alerts)
```

## Troubleshooting

**Dashboard won't start:**
- Check port 5006 is not in use: `netstat -ano | findstr :5006`
- Ensure all dependencies installed: `pip install -r requirements.txt`

**MQTT not connecting:**
- Verify broker address in `config.py`
- Check ESP32 is publishing to correct topics
- Review `mqtt_handler.py` for connection logs

**Database errors:**
- Delete `smart_farm.db` to reset
- Check database path in `config.py`

**Missing modules:**
- Run: `pip install -r requirements.txt`
- Or individually: `pip install panel bokeh pandas`

## Next Steps

1. ✅ Run `python main.py`
2. ✅ Visit `http://localhost:5006`
3. ✅ Explore Dashboard, Analytics, Export pages
4. ✅ Modify settings in `config.py`
5. ✅ Add new pages under `pages/` folder

## Support

For issues or enhancements, refer to:
- README.md - Full documentation
- config.py - All settings
- pages/ - Individual page logic
- utils.py - Reusable functions
