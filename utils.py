# =========================================================
# UTILITIES & HELPERS
# =========================================================

import pandas as pd
from datetime import datetime, timedelta
from config import SENSOR_LABELS, SENSOR_UNITS

# =========================================================
# STATISTICAL FUNCTIONS
# =========================================================

def build_stats_html(df, sensor_key):
    """Build HTML statistics card for a sensor in a time period."""
    label = SENSOR_LABELS.get(sensor_key, sensor_key)
    unit = SENSOR_UNITS.get(sensor_key, "")

    if df.empty:
        return f"""
        <div class='sensor-card'>
            <div style='font-size:18px;font-weight:700;'>{label} Statistics</div>
            <div style='font-size:16px;margin-top:10px;'>No data in selected range.</div>
        </div>
        """

    values = df["Value"].astype(float)
    mean_value = values.mean()
    min_value = values.min()
    max_value = values.max()
    std_value = values.std() if len(values) > 1 else 0.0

    if len(values) >= 2:
        trend_direction = "Rising" if values.iloc[-1] >= values.iloc[0] else "Falling"
        step_slope = (values.iloc[-1] - values.iloc[0]) / (len(values) - 1)
        projected_next = values.iloc[-1] + step_slope
    else:
        trend_direction = "Stable"
        projected_next = values.iloc[-1]

    return f"""
    <div class='sensor-card'>
        <div style='font-size:18px;font-weight:700;'>{label} Statistics</div>
        <div style='display:flex;gap:28px;flex-wrap:wrap;margin-top:12px;font-size:16px;'>
            <div><b>Records:</b> {len(values)}</div>
            <div><b>Mean:</b> {mean_value:.2f}{unit}</div>
            <div><b>Min:</b> {min_value:.2f}{unit}</div>
            <div><b>Max:</b> {max_value:.2f}{unit}</div>
            <div><b>Std Dev:</b> {std_value:.2f}</div>
            <div><b>Trend:</b> {trend_direction}</div>
            <div><b>Next Estimate:</b> {projected_next:.2f}{unit}</div>
        </div>
    </div>
    """

# =========================================================
# DATAFRAME CONVERSIONS
# =========================================================

def to_export_dataframe(df):
    """Convert dataframe to pivot format with sensors as columns."""
    if df.empty:
        return pd.DataFrame(columns=["Timestamp"])

    # Pivot: each sensor becomes a column
    pivot_df = df.pivot_table(
        index="Timestamp",
        columns="Sensor",
        values="Value",
        aggfunc="first"
    )
    
    # Format timestamp in index
    pivot_df.index = pd.to_datetime(pivot_df.index).strftime("%Y-%m-%d %H:%M:%S")
    pivot_df.index.name = "Timestamp"
    
    # Reset index to make Timestamp a column
    pivot_df = pivot_df.reset_index()
    
    return pivot_df

def dataframe_to_markdown(df):
    """Convert pivoted dataframe to Markdown table format."""
    if df.empty:
        return "| No data available |\n"

    # Generate header from column names
    header = "| " + " | ".join(df.columns) + " |\n"
    separator = "|" + "|".join(["---" for _ in df.columns]) + "|\n"
    
    lines = [header, separator]
    for _, row in df.iterrows():
        row_str = "| " + " | ".join(str(v) for v in row.values) + " |\n"
        lines.append(row_str)

    return "".join(lines)

# =========================================================
# TIME WINDOW HELPERS
# =========================================================

def get_range_window(range_name, start_picker=None, end_picker=None):
    """Get start and end time from range name or custom pickers."""
    end_time = datetime.now()

    delta_map = {
        "Last 1 hour": timedelta(hours=1),
        "Last 2 hours": timedelta(hours=2),
        "Last 4 hours": timedelta(hours=4),
        "Last 8 hours": timedelta(hours=8),
        "Last 16 hours": timedelta(hours=16),
        "Last 24 hours": timedelta(hours=24),
        "Last 7 days": timedelta(days=7),
        "Last 30 days": timedelta(days=30),
    }

    if range_name in delta_map:
        return end_time - delta_map[range_name], end_time

    if range_name == "All time":
        return None, None

    if start_picker and end_picker:
        return start_picker.value, end_picker.value

    return None, None
