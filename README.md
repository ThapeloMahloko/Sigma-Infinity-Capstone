# Smart Farm Dashboard - Modular Structure

This is a refactored version of the monolithic smart farm dashboard into a modular, maintainable architecture.

## Folder Structure

```
smart_farm_dashboard/
├── main.py                 # Entry point - ties everything together
├── config.py               # All configuration settings
├── database.py             # Database models and session management
├── mqtt_handler.py         # MQTT connection and message handling
├── ui_components.py        # Shared UI components (cards, plots, etc.)
├── utils.py                # Helper functions (stats, exports, time windows)
├── requirements.txt        # Python dependencies
├── pages/                  # Individual page modules
│   ├── __init__.py
│   ├── dashboard.py        # Dashboard page (live sensors + trends)
│   ├── analytics.py        # Analytics page (historical data + filters)
│   ├── export.py           # Data export page (10 download options)
│   ├── controls.py         # Controls page (fan, pump, alarm, feeder)
│   └── telegram.py         # Telegram bot page (QR + notifications)
└── README.md               # This file
```

## How to Run

1. **Install dependencies:**
   ```bash
   cd smart_farm_dashboard
   pip install -r requirements.txt
   ```

2. **Run the dashboard:**
   ```bash
   python main.py
   ```

3. **Open browser:**
   - Automatic: `http://localhost:5006`
   - Manual: `http://localhost:5006`

## Key Modules

### config.py
- MQTT settings
- Database configuration
- Sensor definitions (topics, labels, units)
- UI colors and styling
- Panel/server settings

### database.py
- SQLAlchemy ORM models
- Database session management
- Helper functions for saving sensor data

### mqtt_handler.py
- MQTT client setup
- Connection and message callbacks
- Real-time data updates to UI
- Thread-safe state management

### ui_components.py
- Shared Panel widgets (cards, plots)
- CSS styling
- Live data storage
- Refresh callbacks

### pages/
Each page is its own module for easy maintenance:
- **dashboard.py**: Live sensor cards + trends graph
- **analytics.py**: Historical data filtering, plotting, statistics
- **export.py**: 10 export format options with filtering
- **controls.py**: MQTT-based device controls
- **telegram.py**: Bot setup and notifications

### utils.py
- Statistical analysis functions
- Data format conversions (CSV, JSON, etc.)
- Time window helpers
- HTML/Markdown generation

## Adding New Features

### To add a new sensor:
1. Add to `SENSOR_TOPICS` in `config.py`
2. Add to `SENSOR_LABELS` and `SENSOR_UNITS`
3. It will automatically appear in all dropdowns

### To add a new page:
1. Create new file in `pages/` folder
2. Define your page layout
3. Import and add to navigation in `main.py`

### To modify styling:
- Edit CSS in `ui_components.py`
- Update colors in `config.py`

## Benefits of This Structure

✅ **Modular**: Each component has a single responsibility
✅ **Maintainable**: Easy to find and update code
✅ **Scalable**: Add new sensors/pages without modifying core files
✅ **Testable**: Easier to unit test individual modules
✅ **Reusable**: Import utils/components into other projects
✅ **Configuration**: Centralized settings in `config.py`

## Future Enhancements

- Add authentication/login page
- Add email alerts module
- Add data backup/restore utilities
- Add real-time notifications module
- Add user preferences storage
- Add custom report generation
