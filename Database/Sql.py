"""
Database module for Smart Farm sensor readings.

Provides ORM models and database session management for storing
and querying sensor data from MQTT topics.
"""

from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager
from datetime import datetime

# Database configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "sensor_data.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Base class for ORM models
Base = declarative_base()

# Create engine and session factory
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class SensorReading(Base):
    """
    ORM model for sensor readings.
    
    One row represents a complete set of sensor measurements captured
    at a single timestamp. This flat structure prevents the "staircase"
    effect caused by recording each sensor event as a separate row.
    """
    __tablename__ = 'sensor_readings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    soil_moisture = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    water_level = Column(Float, nullable=True)
    ambient_light = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    motion_detection = Column(Float, nullable=True)
    ultrasonic_distance = Column(Float, nullable=True)
    pump_status = Column(Float, nullable=True)
    fan_status = Column(Float, nullable=True)

    def __repr__(self):
        return (f"<Reading {self.timestamp:%Y-%m-%d %H:%M:%S} | "
                f"T={self.temperature}°C, H={self.humidity}%, "
                f"L={self.ambient_light} lux>")


def init_db():
    """Initialize the database, creating tables if they don't exist."""
    Base.metadata.create_all(engine)


@contextmanager
def get_session():
    """
    Context manager for database sessions.
    
    Usage:
        with get_session() as session:
            readings = session.query(SensorReading).all()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

