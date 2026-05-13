"""
Minimal test app to verify Panel rendering works on Hugging Face Spaces.
"""

import panel as pn

# Enable panel extensions
pn.extension('plotly')

# Simple test dashboard
test_dashboard = pn.Column(
    pn.pane.Markdown("# 🌱 Smart Farm Dashboard"),
    pn.pane.Markdown("## Test Version - App is Running!"),
    pn.widgets.IntSlider(name="Test Slider", start=0, end=100, value=50),
    sizing_mode="stretch_width"
)

# Mark as servable for Panel's automatic serving
test_dashboard.servable()
