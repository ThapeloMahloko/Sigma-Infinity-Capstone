from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "sensor_data.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class SensorReading(Base):
    """Single sensor event stored with a timestamp and optional denormalized fields."""

    __tablename__ = "farm_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    topic = Column(String(255), nullable=False, index=True)
    sensor_name = Column(String(64), nullable=True, index=True)
    value = Column(Float, nullable=True)
    raw_payload = Column(Text, nullable=True)
    soil_moisture = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    water_level = Column(Float, nullable=True)
    ambient_light = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    motion_detection = Column(Boolean, nullable=True)
    ultrasonic_distance = Column(Float, nullable=True)
    pump_status = Column(Boolean, nullable=True)
    fan_status = Column(Boolean, nullable=True)

    def __repr__(self) -> str:
        sensor_bits = []
        for field_name in (
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
        ):
            value = getattr(self, field_name)
            if value is not None:
                sensor_bits.append(f"{field_name}={value}")

        details = ", ".join(sensor_bits) if sensor_bits else self.raw_payload or "no data"
        return f"<SensorReading {self.timestamp:%Y-%m-%d %H:%M:%S} {self.topic} {details}>"


def init_db() -> None:
    """Create the SQLite database and table if they do not already exist."""

    Base.metadata.create_all(engine)


def get_session():
    """Return a new SQLAlchemy session bound to the project database."""

    return SessionLocal()


# Backwards-compatible alias for the existing code in this repository.
Session = SessionLocal

