from __future__ import annotations

from datetime import datetime

try:
    from .Sql import DATABASE_PATH, SensorReading, get_session, init_db
except ImportError:
    from Sql import DATABASE_PATH, SensorReading, get_session, init_db


def main() -> None:
    init_db()
    with get_session() as session:
        reading_count = session.query(SensorReading).count()

    print(f"SQLite database ready: {DATABASE_PATH}")
    print(f"Current reading rows: {reading_count}")


if __name__ == "__main__":
    main()
