# =========================================================
# DASHBOARD PAGE
# =========================================================

import panel as pn
from ui_components import (
    hero, temp_card, humidity_card, soil_card,
    water_card, light_card, rain_card, fan_card,
    status_card, plot, sensor_selector
)

dashboard_page = pn.Column(
    hero,

    pn.Row(
        temp_card,
        humidity_card,
        soil_card
    ),

    pn.Row(
        water_card,
        light_card,
        rain_card
    ),

    pn.Row(
        fan_card
    ),

    status_card,

    pn.Column(
        pn.Row(
            pn.pane.Markdown("## Live Sensor Trends"),
            sensor_selector
        ),
        plot,
        css_classes=["section-box"]
    )
)
