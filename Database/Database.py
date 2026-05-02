"""
Database initialization and status utility.

Run this script to initialize the database and check the number of sensor readings.
"""

from __future__ import annotations
from datetime import datetime

try:
    from .Sql import DATABASE_PATH, SensorReading, get_session, init_db
except ImportError:
    from Sql import DATABASE_PATH, SensorReading, get_session, init_db


def main() -> None:
    """Initialize the database and display status."""
    init_db()
    
    with get_session() as session:
        reading_count = session.query(SensorReading).count()
        if reading_count > 0:
            latest = session.query(SensorReading).order_by(SensorReading.timestamp.desc()).first()
            print(f"📁 Database: {DATABASE_PATH}")
            print(f"📊 Total readings: {reading_count}")
            print(f"⏱️  Latest reading: {latest.timestamp}")
        else:
            print(f"📁 Database: {DATABASE_PATH}")
            print(f"📊 Total readings: {reading_count}")
            print("💡 No data yet. Run subscriber.py to start collecting data.")


if __name__ == "__main__":
    main()
