# =========================================================
# EXPORT PAGE
# =========================================================

import panel as pn
import pandas as pd
import io
import sqlite3
import zipfile
from datetime import datetime, timedelta

from config import SENSOR_LABELS, SENSOR_UNITS, COLOR_TEXT_MUTED
from database import Session, SensorData
from utils import get_range_window, to_export_dataframe, dataframe_to_markdown

# =========================================================
# EXPORT WIDGETS
# =========================================================

export_scope = pn.widgets.Select(
    name="Dataset Scope",
    options=["Selected sensor only", "All sensors"],
    value="Selected sensor only"
)

export_sensor = pn.widgets.Select(
    name="Sensor",
    options={SENSOR_LABELS[key]: key for key in SENSOR_LABELS},
    value="temperature"
)

export_range = pn.widgets.Select(
    name="Range",
    options=[
        "All time",
        "Last 1 hour",
        "Last 2 hours",
        "Last 4 hours",
        "Last 8 hours",
        "Last 16 hours",
        "Last 24 hours",
        "Last 7 days",
        "Last 30 days",
        "Custom"
    ],
    value="All time"
)

export_start = pn.widgets.DatetimePicker(
    name="Start Date/Time",
    value=datetime.now() - timedelta(hours=24)
)

export_end = pn.widgets.DatetimePicker(
    name="End Date/Time",
    value=datetime.now()
)

export_apply_btn = pn.widgets.Button(
    name="Refresh Export Dataset",
    button_type="success"
)

export_status = pn.pane.Markdown("Ready to export.")

export_table = pn.widgets.Tabulator(
    pd.DataFrame(),
    height=500,
    sizing_mode="stretch_width"
)

# =========================================================
# EXPORT FUNCTIONS
# =========================================================

def resolve_export_window():
    range_name = export_range.value

    if range_name == "All time":
        return None, None

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

    return export_start.value, export_end.value

def sync_export_datetime_pickers(event=None):
    if export_range.value == "Custom" or export_range.value == "All time":
        return

    start_time, end_time = resolve_export_window()
    export_start.value = start_time
    export_end.value = end_time

def toggle_export_sensor(event=None):
    export_sensor.disabled = export_scope.value == "All sensors"

def fetch_export_dataframe():
    start_time, end_time = resolve_export_window()

    if export_range.value == "Custom":
        if start_time is None or end_time is None:
            raise ValueError("Please provide both start and end date/time for custom export.")
        if start_time > end_time:
            raise ValueError("Start date/time must be before end date/time.")

    local_session = Session()

    try:
        query = local_session.query(SensorData)

        if export_scope.value == "Selected sensor only":
            query = query.filter(SensorData.sensor == export_sensor.value)

        if start_time is not None:
            query = query.filter(SensorData.timestamp >= start_time)

        if end_time is not None:
            query = query.filter(SensorData.timestamp <= end_time)

        rows = query.order_by(SensorData.timestamp.asc()).all()

        data = [{
            "Sensor": row.sensor,
            "Value": row.value,
            "Timestamp": row.timestamp,
        } for row in rows]

        df = pd.DataFrame(data)
        return df, start_time, end_time

    finally:
        local_session.close()

def update_export_preview(event=None):
    try:
        df, start_time, end_time = fetch_export_dataframe()
    except ValueError as exc:
        export_status.object = str(exc)
        export_table.value = pd.DataFrame(columns=["Timestamp"])
        return

    display_df = to_export_dataframe(df)
    if "Timestamp" in display_df.columns:
        export_table.value = display_df.sort_values(by="Timestamp", ascending=False).head(1000)
    else:
        export_table.value = display_df.head(1000)

    if start_time is None and end_time is None:
        time_label = "all available time"
    else:
        time_label = f"{start_time:%Y-%m-%d %H:%M} to {end_time:%Y-%m-%d %H:%M}"

    scope_label = export_sensor.value if export_scope.value == "Selected sensor only" else "all sensors"
    export_status.object = f"Prepared {len(display_df)} rows for {scope_label} over {time_label}."

def export_current_df():
    df, _, _ = fetch_export_dataframe()
    return to_export_dataframe(df)

# =========================================================
# DOWNLOAD CALLBACKS (10 OPTIONS)
# =========================================================

def download_sqlite_db():
    return "smart_farm.db"

def download_sql_dump():
    conn = sqlite3.connect("smart_farm.db")
    try:
        dump_text = "\n".join(conn.iterdump())
    finally:
        conn.close()
    return io.BytesIO(dump_text.encode("utf-8"))

def download_csv_data():
    df = export_current_df()
    return io.BytesIO(df.to_csv(index=False).encode("utf-8"))

def download_excel_data():
    df = export_current_df()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="sensor_data")
    output.seek(0)
    return output

def download_json_data():
    df = export_current_df()
    return io.BytesIO(df.to_json(orient="records", indent=2).encode("utf-8"))

def download_tsv_data():
    df = export_current_df()
    return io.BytesIO(df.to_csv(index=False, sep="\t").encode("utf-8"))

def download_xml_data():
    df = export_current_df()
    xml_text = df.to_xml(index=False, root_name="sensor_data", row_name="row")
    return io.BytesIO(xml_text.encode("utf-8"))

def download_html_data():
    df = export_current_df()
    return io.BytesIO(df.to_html(index=False).encode("utf-8"))

def download_markdown_data():
    df = export_current_df()
    markdown_text = dataframe_to_markdown(df)
    return io.BytesIO(markdown_text.encode("utf-8"))

def download_zip_bundle():
    df = export_current_df()
    archive = io.BytesIO()

    csv_text = df.to_csv(index=False)
    json_text = df.to_json(orient="records", indent=2)
    tsv_text = df.to_csv(index=False, sep="\t")
    xml_text = df.to_xml(index=False, root_name="sensor_data", row_name="row")

    xlsx_buffer = io.BytesIO()
    with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="sensor_data")
    xlsx_bytes = xlsx_buffer.getvalue()

    with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("sensor_data.csv", csv_text)
        zf.writestr("sensor_data.json", json_text)
        zf.writestr("sensor_data.tsv", tsv_text)
        zf.writestr("sensor_data.xml", xml_text)
        zf.writestr("sensor_data.xlsx", xlsx_bytes)
        zf.writestr("README.txt", "Bundle contains filtered export in CSV, JSON, TSV, XML, and XLSX formats.")

    archive.seek(0)
    return archive

# =========================================================
# DOWNLOAD BUTTONS
# =========================================================

download_db_btn = pn.widgets.FileDownload(
    callback=download_sqlite_db,
    filename="smart_farm.db",
    button_type="success",
    label="1) Full Database (.db)"
)

download_sql_btn = pn.widgets.FileDownload(
    callback=download_sql_dump,
    filename="smart_farm_dump.sql",
    button_type="primary",
    label="2) SQL Dump (.sql)"
)

download_csv_btn = pn.widgets.FileDownload(
    callback=download_csv_data,
    filename="smart_farm_filtered.csv",
    button_type="primary",
    label="3) Filtered CSV (.csv)"
)

download_excel_btn = pn.widgets.FileDownload(
    callback=download_excel_data,
    filename="smart_farm_filtered.xlsx",
    button_type="primary",
    label="4) Filtered Excel (.xlsx)"
)

download_json_btn = pn.widgets.FileDownload(
    callback=download_json_data,
    filename="smart_farm_filtered.json",
    button_type="primary",
    label="5) Filtered JSON (.json)"
)

download_tsv_btn = pn.widgets.FileDownload(
    callback=download_tsv_data,
    filename="smart_farm_filtered.tsv",
    button_type="primary",
    label="6) Filtered TSV (.tsv)"
)

download_xml_btn = pn.widgets.FileDownload(
    callback=download_xml_data,
    filename="smart_farm_filtered.xml",
    button_type="primary",
    label="7) Filtered XML (.xml)"
)

download_html_btn = pn.widgets.FileDownload(
    callback=download_html_data,
    filename="smart_farm_filtered.html",
    button_type="primary",
    label="8) Filtered HTML (.html)"
)

download_md_btn = pn.widgets.FileDownload(
    callback=download_markdown_data,
    filename="smart_farm_filtered.md",
    button_type="primary",
    label="9) Filtered Markdown (.md)"
)

download_zip_btn = pn.widgets.FileDownload(
    callback=download_zip_bundle,
    filename="smart_farm_filtered_bundle.zip",
    button_type="warning",
    label="10) Filtered Bundle (.zip)"
)

export_range.param.watch(sync_export_datetime_pickers, "value")
export_scope.param.watch(toggle_export_sensor, "value")
export_apply_btn.on_click(update_export_preview)

toggle_export_sensor()
sync_export_datetime_pickers()

def _initialize_export_preview():
    update_export_preview()

pn.state.onload(_initialize_export_preview)

# =========================================================
# EXPORT PAGE LAYOUT
# =========================================================

export_page = pn.Column(
    pn.pane.HTML("""
    <div class='hero'>
    <div style='font-size:14px;letter-spacing:4px;color:%s;'>DATA EXPORT</div>
    <div style='font-size:52px;font-weight:800;color:white;margin-top:10px;'>Historical Data</div>
    </div>
    """ % COLOR_TEXT_MUTED),

    pn.Column(
        pn.Row(
            export_scope,
            export_sensor,
            export_range,
            export_apply_btn
        ),
        pn.Row(
            export_start,
            export_end
        ),
        export_status,
        css_classes=["section-box"]
    ),

    pn.Column(
        pn.Row(
            download_db_btn,
            download_sql_btn,
            download_csv_btn,
            download_excel_btn,
            download_json_btn
        ),
        pn.Row(
            download_tsv_btn,
            download_xml_btn,
            download_html_btn,
            download_md_btn,
            download_zip_btn
        ),
        css_classes=["section-box"]
    ),

    pn.Column(
        export_table,
        css_classes=["section-box"]
    )
)
