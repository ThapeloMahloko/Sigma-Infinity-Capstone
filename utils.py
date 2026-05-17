# =========================================================
# UTILITIES & HELPERS
# =========================================================
"""
Utility Functions Module.

This module provides helper functions for statistical analysis of sensor data,
dataframe conversions for exporting, and time window calculations.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Optional
from config import SENSOR_LABELS, SENSOR_UNITS

# =========================================================
# STATISTICAL FUNCTIONS
# =========================================================

def build_stats_html(df: pd.DataFrame, sensor_key: str) -> str:
    """
    Builds an HTML statistics card for a specific sensor over a given time period.

    Args:
        df (pd.DataFrame): The dataframe containing sensor data. Must have a 'Value' column.
        sensor_key (str): The identifier for the sensor.

    Returns:
        str: An HTML string formatted as a card displaying statistics.
    """
    label = SENSOR_LABELS.get(sensor_key, sensor_key)
    unit = SENSOR_UNITS.get(sensor_key, "")

    if df.empty or "Value" not in df.columns:
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

def to_export_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts a raw sensor dataframe into a pivoted format suitable for exporting,
    where each sensor is represented as a separate column.

    Args:
        df (pd.DataFrame): Raw dataframe with 'Timestamp', 'Sensor', and 'Value' columns.

    Returns:
        pd.DataFrame: A pivoted dataframe with timestamps as rows and sensors as columns.
    """
    if df.empty or "Timestamp" not in df.columns or "Sensor" not in df.columns or "Value" not in df.columns:
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

    # Reset index to make Timestamp a standard column
    pivot_df = pivot_df.reset_index()

    return pivot_df

def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """
    Converts a pivoted dataframe into a Markdown-formatted table string.

    Args:
        df (pd.DataFrame): The pivoted dataframe to convert.

    Returns:
        str: A string representing the dataframe as a Markdown table.
    """
    if df.empty:
        return "| No data available |\n"

    # Generate header from column names
    header = "| " + " | ".join(str(col) for col in df.columns) + " |\n"
    separator = "|" + "|".join(["---" for _ in df.columns]) + "|\n"

    lines = [header, separator]
    for _, row in df.iterrows():
        row_str = "| " + " | ".join(str(v) for v in row.values) + " |\n"
        lines.append(row_str)

    return "".join(lines)

# =========================================================
# TIME WINDOW HELPERS
# =========================================================

def get_range_window(range_name: str, start_picker=None, end_picker=None) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Calculates the start and end datetime based on a predefined range name or custom pickers.

    Args:
        range_name (str): The name of the predefined range (e.g., 'Last 1 hour').
        start_picker: The UI component holding the custom start datetime.
        end_picker: The UI component holding the custom end datetime.

    Returns:
        Tuple[Optional[datetime], Optional[datetime]]: The start and end datetime objects,
                                                       or (None, None) if 'All time'.
    """
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

    if start_picker and end_picker and start_picker.value and end_picker.value:
        return start_picker.value, end_picker.value

    return None, None
