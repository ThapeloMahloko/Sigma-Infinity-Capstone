import argparse
from datetime import datetime, timedelta, timezone
from numbers import Real
import os
import socket

import holoviews as hv
import hvplot.pandas
import pandas as pd
import panel as pn
import param
import sqlalchemy as sa

from Database.Sql import DATABASE_PATH, SensorReading, init_db


pn.extension("tabulator", "plotly", "vega")
hv.extension("plotly")

engine = sa.create_engine(f"sqlite:///{DATABASE_PATH.as_posix()}", echo=False)

DEGREE_C = "\N{DEGREE SIGN}C"
try:
    SMART_FARM_DASHBOARD_REFRESH_MS = int(os.getenv("SMART_FARM_DASHBOARD_REFRESH_MS", "2000"))
except ValueError:
    SMART_FARM_DASHBOARD_REFRESH_MS = 2000

READING_COLUMNS = [
    "id",
    "timestamp",
    "soil_moisture",
    "temperature",
    "humidity",
    "water_level",
    "ambient_light",
    "rainfall",
    "motion_detection",
    "ultrasonic_distance",
    "pump_status",
    "fan_status",
]

DASHBOARD_CSS = """
:root,
html[data-farm-theme="dark"] {
    color-scheme: dark;
    --farm-bg: #07110f;
    --farm-bg-alt: #0d1f1a;
    --farm-surface: rgba(16, 31, 28, 0.94);
    --farm-surface-strong: #142822;
    --farm-border: rgba(135, 214, 177, 0.18);
    --farm-text: #edf8f2;
    --farm-muted: #9fb8ad;
    --farm-heading: #ffffff;
    --farm-primary: #69d391;
    --farm-primary-strong: #28a765;
    --farm-warning: #ffd166;
    --farm-danger: #ff6b6b;
    --farm-info: #6ec6ff;
    --farm-chart-bg: #101f1c;
    --farm-shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
}

html[data-farm-theme="light"],
body.farm-light {
    color-scheme: light;
    --farm-bg: #f4f8f3;
    --farm-bg-alt: #e6f1e8;
    --farm-surface: rgba(255, 255, 255, 0.95);
    --farm-surface-strong: #ffffff;
    --farm-border: rgba(38, 94, 68, 0.15);
    --farm-text: #1b2e26;
    --farm-muted: #63766d;
    --farm-heading: #0d241b;
    --farm-primary: #1f9d62;
    --farm-primary-strong: #0d7b49;
    --farm-warning: #b87503;
    --farm-danger: #c44141;
    --farm-info: #1876a7;
    --farm-chart-bg: #ffffff;
    --farm-shadow: 0 18px 40px rgba(54, 94, 70, 0.14);
}

html,
body {
    background: linear-gradient(180deg, var(--farm-bg) 0%, var(--farm-bg-alt) 100%);
    color: var(--farm-text);
}

#container {
    background: linear-gradient(180deg, var(--farm-bg) 0%, var(--farm-bg-alt) 100%) !important;
    height: auto !important;
    min-height: 100vh !important;
    overflow: auto !important;
}

#content {
    background: transparent !important;
    overflow: visible !important;
}

#main {
    background: transparent !important;
    color: var(--farm-text) !important;
    overflow: visible !important;
    padding: 24px 28px 32px !important;
}

#header {
    border-bottom: 1px solid var(--farm-border) !important;
    box-shadow: none !important;
    min-height: 58px !important;
    padding: 0 22px !important;
    position: static !important;
}

#header .app-header {
    align-items: center !important;
    display: flex !important;
    min-height: 58px !important;
}

#header .title {
    color: var(--farm-heading) !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
    letter-spacing: 0 !important;
    text-decoration: none !important;
}

#header .pn-busy-container {
    align-items: center !important;
    display: flex !important;
    min-height: 58px !important;
}

.bk-root,
.bk-root .container,
.bk-root .main {
    background: transparent !important;
}

.farm-controls {
    margin-bottom: 12px;
    min-height: 40px;
}

.farm-theme-toggle button {
    border-radius: 999px !important;
    font-weight: 700 !important;
    letter-spacing: 0 !important;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14);
}

.farm-hero {
    background:
        linear-gradient(135deg, rgba(105, 211, 145, 0.22), transparent 42%),
        linear-gradient(120deg, var(--farm-surface-strong), var(--farm-surface));
    border: 1px solid var(--farm-border);
    border-radius: 8px;
    box-shadow: var(--farm-shadow);
    color: var(--farm-text);
    overflow: hidden;
    padding: 26px 28px;
}

.farm-hero__kicker,
.farm-section-label {
    color: var(--farm-primary);
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    margin: 0 0 8px;
    text-transform: uppercase;
}

.farm-hero h1 {
    color: var(--farm-heading);
    font-size: clamp(2rem, 3.4vw, 3.6rem);
    font-weight: 850;
    letter-spacing: 0;
    line-height: 1;
    margin: 0;
}

.farm-hero p {
    color: var(--farm-muted);
    font-size: 1rem;
    margin: 10px 0 0;
}

.farm-hero__meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
}

.farm-chip,
.status-pill {
    align-items: center;
    background: color-mix(in srgb, var(--farm-surface-strong), transparent 18%);
    border: 1px solid var(--farm-border);
    border-radius: 999px;
    color: var(--farm-text);
    display: inline-flex;
    font-size: 0.84rem;
    font-weight: 700;
    gap: 8px;
    padding: 8px 12px;
}

.freshness-dot {
    background: var(--accent, var(--farm-primary));
    border-radius: 50%;
    box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent, var(--farm-primary)), transparent 82%);
    display: inline-flex;
    height: 9px;
    width: 9px;
}

.farm-card {
    background: var(--farm-surface);
    border: 1px solid var(--farm-border);
    border-radius: 8px;
    box-shadow: var(--farm-shadow);
    color: var(--farm-text);
    min-height: 146px;
    overflow: hidden;
    padding: 18px;
    position: relative;
    transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.farm-card::before {
    background: linear-gradient(90deg, var(--accent), transparent);
    content: "";
    height: 4px;
    left: 0;
    position: absolute;
    right: 0;
    top: 0;
}

.farm-card:hover {
    border-color: color-mix(in srgb, var(--accent), var(--farm-border) 45%);
    transform: translateY(-3px);
}

.metric-card__top {
    align-items: center;
    display: flex;
    justify-content: space-between;
}

.metric-icon {
    align-items: center;
    background: color-mix(in srgb, var(--accent), transparent 82%);
    border: 1px solid color-mix(in srgb, var(--accent), transparent 55%);
    border-radius: 8px;
    color: var(--accent);
    display: inline-flex;
    font-size: 1.35rem;
    height: 42px;
    justify-content: center;
    width: 42px;
}

.metric-unit {
    color: var(--farm-muted);
    font-size: 0.82rem;
    font-weight: 800;
}

.metric-value {
    color: var(--farm-heading);
    font-size: clamp(2rem, 3vw, 3rem);
    font-weight: 900;
    letter-spacing: 0;
    line-height: 1;
    margin-top: 18px;
}

.metric-label {
    color: var(--farm-muted);
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    margin-top: 8px;
    text-transform: uppercase;
}

.status-strip {
    background: var(--farm-surface);
    border: 1px solid var(--farm-border);
    border-radius: 8px;
    box-shadow: var(--farm-shadow);
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 14px;
}

.status-dot {
    background: var(--accent);
    border-radius: 50%;
    box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent), transparent 82%);
    height: 9px;
    width: 9px;
}

.status-pill strong {
    color: var(--farm-heading);
}

.farm-chart-card,
.farm-table-wrap {
    background: var(--farm-surface);
    border: 1px solid var(--farm-border);
    border-radius: 8px;
    box-shadow: var(--farm-shadow);
    padding: 14px;
}

.farm-table-wrap .tabulator {
    background: var(--farm-surface-strong) !important;
    border: 0 !important;
    color: var(--farm-text) !important;
    font-size: 0.92rem !important;
}

.farm-table-wrap .tabulator .tabulator-header {
    background: color-mix(in srgb, var(--farm-surface-strong), var(--farm-bg) 18%) !important;
    border-bottom: 1px solid var(--farm-border) !important;
    color: var(--farm-heading) !important;
}

.farm-table-wrap .tabulator .tabulator-header .tabulator-col {
    background: transparent !important;
    border-right: 1px solid var(--farm-border) !important;
    color: var(--farm-heading) !important;
}

.farm-table-wrap .tabulator .tabulator-header .tabulator-col-content {
    padding: 10px 8px !important;
}

.farm-table-wrap .tabulator .tabulator-tableholder {
    background: var(--farm-surface-strong) !important;
}

.farm-table-wrap .tabulator .tabulator-row {
    background: color-mix(in srgb, var(--farm-surface), var(--farm-bg) 8%) !important;
    border-bottom: 1px solid color-mix(in srgb, var(--farm-border), transparent 35%) !important;
    color: var(--farm-text) !important;
}

.farm-table-wrap .tabulator .tabulator-row:nth-child(even) {
    background: color-mix(in srgb, var(--farm-surface-strong), var(--farm-bg) 16%) !important;
}

.farm-table-wrap .tabulator .tabulator-row:hover {
    background: color-mix(in srgb, var(--farm-primary), var(--farm-surface) 82%) !important;
}

.farm-table-wrap .tabulator .tabulator-cell {
    border-right: 1px solid var(--farm-border) !important;
    color: var(--farm-text) !important;
}

.farm-table-wrap .tabulator .tabulator-placeholder {
    background: var(--farm-surface-strong) !important;
    color: var(--farm-muted) !important;
}

.farm-table-wrap .tabulator ::-webkit-scrollbar {
    height: 12px;
    width: 12px;
}

.farm-table-wrap .tabulator ::-webkit-scrollbar-track {
    background: color-mix(in srgb, var(--farm-surface-strong), #000 18%);
}

.farm-table-wrap .tabulator ::-webkit-scrollbar-thumb {
    background: color-mix(in srgb, var(--farm-primary), var(--farm-surface) 48%);
    border-radius: 999px;
}

.farm-chart-empty {
    align-items: center;
    color: var(--farm-muted);
    display: flex;
    font-weight: 700;
    height: 280px;
    justify-content: center;
    text-align: center;
}

.nav-tabs {
    border-bottom-color: var(--farm-border) !important;
}

.nav-tabs .nav-link {
    border-radius: 8px 8px 0 0 !important;
    color: var(--farm-muted) !important;
    font-weight: 800;
}

.nav-tabs .nav-link.active {
    background: var(--farm-surface) !important;
    border-color: var(--farm-border) var(--farm-border) transparent !important;
    color: var(--farm-heading) !important;
}

.tab-content {
    padding-top: 14px;
}

@media (max-width: 900px) {
    #main {
        padding: 18px 14px 24px !important;
    }

    .farm-hero {
        padding: 22px;
    }
}
"""

PALETTES = {
    "dark": {
        "primary": "#69d391",
        "success": "#69d391",
        "warning": "#ffd166",
        "danger": "#ff6b6b",
        "info": "#6ec6ff",
        "purple": "#c084fc",
        "muted": "#9fb8ad",
        "text": "#edf8f2",
        "grid": "rgba(237, 248, 242, 0.16)",
        "chart_bg": "#101f1c",
    },
    "light": {
        "primary": "#1f9d62",
        "success": "#1f9d62",
        "warning": "#b87503",
        "danger": "#c44141",
        "info": "#1876a7",
        "purple": "#8b5cf6",
        "muted": "#63766d",
        "text": "#1b2e26",
        "grid": "rgba(27, 46, 38, 0.14)",
        "chart_bg": "#ffffff",
    },
}

THEME_VARS = {
    "dark": {
        "--farm-bg": "#07110f",
        "--farm-bg-alt": "#0d1f1a",
        "--farm-surface": "rgba(16, 31, 28, 0.94)",
        "--farm-surface-strong": "#142822",
        "--farm-border": "rgba(135, 214, 177, 0.18)",
        "--farm-text": "#edf8f2",
        "--farm-muted": "#9fb8ad",
        "--farm-heading": "#ffffff",
        "--farm-primary": "#69d391",
        "--farm-primary-strong": "#28a765",
        "--farm-warning": "#ffd166",
        "--farm-danger": "#ff6b6b",
        "--farm-info": "#6ec6ff",
        "--farm-chart-bg": "#101f1c",
        "--farm-shadow": "0 18px 45px rgba(0, 0, 0, 0.28)",
    },
    "light": {
        "--farm-bg": "#f4f8f3",
        "--farm-bg-alt": "#e6f1e8",
        "--farm-surface": "rgba(255, 255, 255, 0.95)",
        "--farm-surface-strong": "#ffffff",
        "--farm-border": "rgba(38, 94, 68, 0.15)",
        "--farm-text": "#1b2e26",
        "--farm-muted": "#63766d",
        "--farm-heading": "#0d241b",
        "--farm-primary": "#1f9d62",
        "--farm-primary-strong": "#0d7b49",
        "--farm-warning": "#b87503",
        "--farm-danger": "#c44141",
        "--farm-info": "#1876a7",
        "--farm-chart-bg": "#ffffff",
        "--farm-shadow": "0 18px 40px rgba(54, 94, 70, 0.14)",
    },
}

pn.config.raw_css.append(DASHBOARD_CSS)


class RealtimeDashboardState(param.Parameterized):
    df = param.Parameter(default=pd.DataFrame(columns=READING_COLUMNS))


def empty_readings_frame():
    return pd.DataFrame(columns=READING_COLUMNS)


def load_sensor_data():
    """Load sensor data from database."""
    try:
        init_db()
        df = pd.read_sql_table(SensorReading.__tablename__, engine)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df.sort_values("timestamp")
    except Exception as exc:
        print(f"Error loading data: {exc}")
        return empty_readings_frame()


def is_missing(value):
    """Return True when a scalar value is None or NaN."""
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def get_latest_readings(df):
    """Get the most recent non-empty reading for each sensor field."""
    if df.empty:
        return {}

    latest = df.iloc[-1].to_dict()
    sensor_fields = (
        "temperature",
        "humidity",
        "ambient_light",
        "water_level",
        "soil_moisture",
        "rainfall",
        "motion_detection",
        "ultrasonic_distance",
        "pump_status",
        "fan_status",
    )

    for field in sensor_fields:
        if field not in df:
            continue
        values = df[field].dropna()
        latest[field] = values.iloc[-1] if not values.empty else None

    return latest


def format_number(value, digits=1):
    if is_missing(value):
        return "N/A"
    if isinstance(value, Real) and not isinstance(value, bool):
        return f"{value:.{digits}f}"
    return str(value)


def format_stat(series, reducer, unit=""):
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return "N/A"
    value = getattr(values, reducer)()
    return f"{value:.1f}{unit}"


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def coerce_timestamp(timestamp):
    if is_missing(timestamp):
        return None
    converted = pd.to_datetime(timestamp, errors="coerce")
    if pd.isna(converted):
        return None
    return converted.to_pydatetime()


def latest_database_timestamp(df):
    if df.empty or "timestamp" not in df:
        return None
    timestamps = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
    if timestamps.empty:
        return None
    return timestamps.max().to_pydatetime()


def format_age(seconds):
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    return f"{hours}h ago"


def freshness_status(latest_timestamp):
    latest_dt = coerce_timestamp(latest_timestamp)
    if latest_dt is None:
        return "No data", "Waiting for sensor rows", "var(--farm-danger)"

    age_seconds = (utc_now() - latest_dt).total_seconds()
    if age_seconds <= 15:
        return "Live", format_age(age_seconds), "var(--farm-primary)"
    if age_seconds <= 60:
        return "Delayed", format_age(age_seconds), "var(--farm-warning)"
    return "Stale", format_age(age_seconds), "var(--farm-danger)"


def recent_window(df, hours=24):
    if df.empty or "timestamp" not in df:
        return empty_readings_frame()
    cutoff = utc_now() - timedelta(hours=hours)
    timestamps = pd.to_datetime(df["timestamp"], errors="coerce")
    return df[timestamps >= cutoff]


def timeframe_to_hours(label):
    mapping = {
        "1H": 1,
        "6H": 6,
        "24H": 24,
        "7D": 24 * 7,
        "30D": 24 * 30,
    }
    return mapping.get(label, 24)


def create_metric_card(label, value, unit, accent, icon):
    """Create a styled metric card."""
    return pn.pane.HTML(
        f"""
        <div class="farm-card" style="--accent: {accent};">
            <div class="metric-card__top">
                <span class="metric-icon">{icon}</span>
                <span class="metric-unit">{unit or "&nbsp;"}</span>
            </div>
            <div class="metric-value">{format_number(value)}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        sizing_mode="stretch_width",
    )


def create_header(latest_timestamp, row_count=0):
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latest_dt = coerce_timestamp(latest_timestamp)
    latest_data = latest_dt.strftime("%Y-%m-%d %H:%M:%S") if latest_dt else "N/A"
    freshness_label, freshness_age, freshness_accent = freshness_status(latest_timestamp)

    return pn.pane.HTML(
        f"""
        <section class="farm-hero">
            <p class="farm-hero__kicker">Live field intelligence</p>
            <h1>&#127806; Smart Farm Dashboard</h1>
            <p>Sensor telemetry, operating status, and 24-hour field trends in one clean view.</p>
            <div class="farm-hero__meta">
                <span class="farm-chip" style="--accent: {freshness_accent};">
                    <span class="freshness-dot"></span>
                    {freshness_label}: {freshness_age}
                </span>
                <span class="farm-chip">Latest data: {latest_data}</span>
                <span class="farm-chip">Dashboard refresh: {updated_at}</span>
                <span class="farm-chip">Rows: {row_count}</span>
            </div>
        </section>
        """,
        sizing_mode="stretch_width",
    )


def create_status_strip(latest, palette, latest_timestamp=None):
    def bool_status(value, on_label, off_label):
        if is_missing(value):
            return "N/A"
        return on_label if bool(value) else off_label

    freshness_label, freshness_age, freshness_accent = freshness_status(latest_timestamp)
    statuses = [
        ("Data", f"{freshness_label} ({freshness_age})", freshness_accent),
        ("Pump", bool_status(latest.get("pump_status"), "Active", "Idle"), palette["success"]),
        ("Fan", bool_status(latest.get("fan_status"), "Running", "Off"), palette["info"]),
        ("Motion", bool_status(latest.get("motion_detection"), "Detected", "Clear"), palette["warning"]),
        ("Rainfall", f"{format_number(latest.get('rainfall'))} mm", palette["purple"]),
    ]

    pills = "\n".join(
        f"""
        <span class="status-pill" style="--accent: {accent};">
            <span class="status-dot"></span>
            <span>{label}</span>
            <strong>{value}</strong>
        </span>
        """
        for label, value, accent in statuses
    )

    return pn.pane.HTML(f'<div class="status-strip">{pills}</div>', sizing_mode="stretch_width")


def create_metric_grid(latest, dark_mode):
    palette = PALETTES["dark" if dark_mode else "light"]
    return pn.GridBox(
        create_metric_card("Temperature", latest.get("temperature"), "&deg;C", palette["danger"], "&#127777;"),
        create_metric_card("Humidity", latest.get("humidity"), "%", palette["info"], "&#128167;"),
        create_metric_card("Soil Moisture", latest.get("soil_moisture"), "%", palette["success"], "&#127793;"),
        create_metric_card("Water Level", latest.get("water_level"), "%", palette["primary"], "&#128688;"),
        create_metric_card("Light", latest.get("ambient_light"), "lux", palette["warning"], "&#9728;"),
        create_metric_card("Rainfall", latest.get("rainfall"), "mm", palette["purple"], "&#127783;"),
        ncols=6,
        sizing_mode="stretch_width",
    )


def create_chart(series_df, y, title, color, dark_mode):
    palette = PALETTES["dark" if dark_mode else "light"]
    if series_df.empty or y not in series_df or series_df[y].dropna().empty:
        return pn.pane.HTML(
            f'<div class="farm-chart-empty">{title}<br>No data available</div>',
            sizing_mode="stretch_width",
        )

    def apply_plot_theme(plot, _element):
        layout = plot.state.setdefault("layout", {})
        layout["paper_bgcolor"] = palette["chart_bg"]
        layout["font"] = {"color": palette["text"]}
        for axis_name in ("xaxis", "yaxis"):
            axis = layout.setdefault(axis_name, {})
            axis["color"] = palette["text"]
            axis["gridcolor"] = palette["grid"]
            axis["zerolinecolor"] = palette["grid"]

    chart_df = series_df.dropna(subset=[y])
    chart = chart_df.hvplot(
        x="timestamp",
        y=y,
        title=title,
        line_width=3,
        color=color,
        responsive=True,
        height=280,
        grid=True,
    ).opts(bgcolor=palette["chart_bg"], hooks=[apply_plot_theme])

    return pn.Column(
        pn.pane.HoloViews(chart, sizing_mode="stretch_width"),
        css_classes=["farm-chart-card"],
        sizing_mode="stretch_width",
    )


def create_charts_panel(series_df, dark_mode, timeframe_label):
    palette = PALETTES["dark" if dark_mode else "light"]
    return pn.Column(
        pn.pane.HTML(
            f'<p class="farm-section-label">Trend Window: {timeframe_label}</p>',
            sizing_mode="stretch_width",
        ),
        pn.GridBox(
            create_chart(series_df, "temperature", f"Temperature Trend ({timeframe_label})", palette["danger"], dark_mode),
            create_chart(series_df, "humidity", f"Humidity Trend ({timeframe_label})", palette["info"], dark_mode),
            create_chart(series_df, "ambient_light", f"Ambient Light ({timeframe_label})", palette["warning"], dark_mode),
            ncols=3,
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
    )


def create_stats_table(stats_df, dark_mode):
    # Ensure missing values are presented clearly in the UI
    display_df = stats_df.fillna("N/A")
    return pn.Column(
        pn.widgets.Tabulator(
            display_df,
            disabled=True,
            show_index=False,
            theme="midnight" if dark_mode else "bootstrap5",
            layout="fit_data_stretch",
            height=260,
            sizing_mode="stretch_width",
        ),
        css_classes=["farm-table-wrap"],
        sizing_mode="stretch_width",
    )


def create_recent_data_table(df, dark_mode):
    if df.empty or "timestamp" not in df:
        recent_df = empty_readings_frame()
    else:
        recent_df = df.sort_values("timestamp", ascending=False).head(50).copy()
    
    # Batch-process rows to propagate sensor values to sensor_name if missing
    if not recent_df.empty:
        sensor_columns = [
            "soil_moisture", "temperature", "humidity", "water_level",
            "ambient_light", "rainfall", "motion_detection", "ultrasonic_distance",
            "pump_status", "fan_status"
        ]
    
    # Fill remaining NaN with "N/A" for UI display
    recent_display = recent_df.fillna("-")
    return pn.Column(
        pn.widgets.Tabulator(
            recent_display,
            show_index=False,
            theme="midnight" if dark_mode else "bootstrap5",
            layout="fit_data_stretch",
            height=430,
            sizing_mode="stretch_width"
        ),
        css_classes=["farm-table-wrap"],
        sizing_mode="stretch_width",
    )


def build_stats(df):
    metrics = [
        ("Temperature", "temperature", DEGREE_C),
        ("Humidity", "humidity", "%"),
        ("Light Level", "ambient_light", " lux"),
        ("Water Level", "water_level", "%"),
        ("Soil Moisture", "soil_moisture", "%"),
        ("Rainfall", "rainfall", " mm"),
    ]

    rows = []
    for label, column, unit in metrics:
        series = df[column] if column in df else pd.Series(dtype="float64")
        rows.append(
            {
                "Metric": label,
                "Min": format_stat(series, "min", unit),
                "Avg": format_stat(series, "mean", unit),
                "Max": format_stat(series, "max", unit),
            }
        )
    return pd.DataFrame(rows)


def find_available_port(start_port=5006, max_tries=20):
    """Return the first available localhost port starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise OSError(f"No available port found from {start_port} to {start_port + max_tries - 1}")


def env_int(name, default):
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def parse_dashboard_args():
    parser = argparse.ArgumentParser(description="Run the Smart Farm Panel dashboard.")
    parser.add_argument(
        "--host",
        default=os.getenv("SMART_FARM_DASHBOARD_HOST", "127.0.0.1"),
        help="Host interface to bind to. Use 0.0.0.0 for access from other devices on your network.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=env_int("SMART_FARM_DASHBOARD_PORT", 0),
        help="Exact port to use. If omitted, the first free port from --start-port is used.",
    )
    parser.add_argument(
        "--start-port",
        type=int,
        default=env_int("SMART_FARM_DASHBOARD_START_PORT", 5006),
        help="First port to try when --port is not provided.",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the dashboard in the default browser after starting.",
    )
    return parser.parse_args()


def get_lan_ip():
    """Best-effort LAN IP detection for printing a usable network URL."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return None


def dashboard_urls(host, port):
    if host in {"0.0.0.0", "::", ""}:
        urls = [f"http://localhost:{port}"]
        lan_ip = get_lan_ip()
        if lan_ip and not lan_ip.startswith("127."):
            urls.append(f"http://{lan_ip}:{port}")
        return urls

    display_host = "localhost" if host in {"127.0.0.1", "::1"} else host
    return [f"http://{display_host}:{port}"]


def websocket_origins(host, port):
    hosts = {"localhost", "127.0.0.1", socket.gethostname()}
    if host not in {"0.0.0.0", "::", ""}:
        hosts.add(host)

    lan_ip = get_lan_ip()
    if lan_ip:
        hosts.add(lan_ip)

    return [f"{origin_host}:{port}" for origin_host in sorted(hosts) if origin_host]


def create_dashboard():
    """Build the main dashboard."""
    state = RealtimeDashboardState(df=load_sensor_data())

    theme_toggle = pn.widgets.Toggle(
        name="Dark theme",
        value=True,
        icon="moon",
        button_type="primary",
        button_style="solid",
        css_classes=["farm-theme-toggle"],
        width=140,
    )
    timeframe_selector = pn.widgets.RadioButtonGroup(
        name="Chart range",
        options=["1H", "6H", "24H", "7D", "30D"],
        value="24H",
        button_type="primary",
        button_style="outline",
        sizing_mode="fixed",
    )

    theme_script = pn.pane.HTML(width=0, height=0, margin=0, sizing_mode="fixed")

    def apply_theme(dark_mode: bool):
        theme_name = "dark" if dark_mode else "light"
        vars_map = THEME_VARS[theme_name]

        theme_toggle.name = "Dark theme" if dark_mode else "Light theme"
        theme_toggle.icon = "moon" if dark_mode else "sun"
        theme_toggle.button_type = "primary" if dark_mode else "light"

        set_vars = "\n".join(
            [f'document.documentElement.style.setProperty("{k}", "{v}");' for k, v in vars_map.items()]
        )
        theme_script.object = f"""
        <script>
            document.documentElement.dataset.farmTheme = "{theme_name}";
            document.body.classList.toggle("farm-dark", {str(dark_mode).lower()});
            document.body.classList.toggle("farm-light", {str((not dark_mode)).lower()});
            document.documentElement.style.colorScheme = "{theme_name}";
            {set_vars}
        </script>
        """

    apply_theme(theme_toggle.value)

    def on_toggle_theme(event):
        apply_theme(bool(event.new))

    theme_toggle.param.watch(on_toggle_theme, "value")

    control_bar = pn.Row(
        pn.Spacer(),
        timeframe_selector,
        theme_toggle,
        css_classes=["farm-controls"],
        sizing_mode="stretch_width",
    )

    header = pn.bind(
        lambda df: create_header(latest_database_timestamp(df), len(df)),
        state.param.df,
    )
    metric_cards = pn.bind(
        lambda df, dark: create_metric_grid(get_latest_readings(df), dark),
        state.param.df,
        theme_toggle,
    )
    status_strip = pn.bind(
        lambda df, dark: create_status_strip(
            get_latest_readings(df),
            PALETTES["dark" if dark else "light"],
            latest_database_timestamp(df),
        ),
        state.param.df,
        theme_toggle,
    )
    charts_panel = pn.bind(
        lambda df, dark, range_label: create_charts_panel(
            recent_window(df, hours=timeframe_to_hours(range_label)),
            dark,
            range_label,
        ),
        state.param.df,
        theme_toggle,
        timeframe_selector,
    )
    stats_table = pn.bind(
        lambda df, dark: create_stats_table(build_stats(df), dark),
        state.param.df,
        theme_toggle,
    )
    data_table = pn.bind(
        lambda df, dark: create_recent_data_table(df, dark),
        state.param.df,
        theme_toggle,
    )

    def refresh_data():
        state.df = load_sensor_data()

    dashboard = pn.template.BootstrapTemplate(
        title="Smart Farm Dashboard",
        header_background="#07110f",
        sidebar_width=0,
    )
    dashboard._smart_farm_refresh_callback = pn.state.add_periodic_callback(
        refresh_data,
        period=SMART_FARM_DASHBOARD_REFRESH_MS,
    )

    dashboard.main[:] = [
        theme_script,
        control_bar,
        header,
        pn.Spacer(height=16),
        metric_cards,
        pn.Spacer(height=16),
        status_strip,
        pn.Spacer(height=16),
        pn.Tabs(
            ("Charts", charts_panel),
            ("Statistics", stats_table),
            ("Recent Data", data_table),
            dynamic=True,
            sizing_mode="stretch_width",
        ),
    ]

    return dashboard


if __name__ == "__main__":
    args = parse_dashboard_args()
    dashboard = create_dashboard()
    port = args.port or find_available_port(start_port=args.start_port)
    origins = websocket_origins(args.host, port)
    urls = dashboard_urls(args.host, port)

    print(f"Smart Farm Dashboard binding to {args.host}:{port}", flush=True)
    for url in urls:
        print(f"Open: {url}", flush=True)

    dashboard.show(
        port=port,
        address=args.host,
        websocket_origin=origins,
        open=args.open_browser,
    )
