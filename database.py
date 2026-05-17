# =========================================================
# DATABASE MODULE
# =========================================================
"""
Database Management Module.

This module handles the SQLAlchemy setup, engine creation, session management,
and provides helper functions for saving sensor data to the database.
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from config import DATABASE_URL

# =========================================================
# DATABASE SETUP
# =========================================================

# Initialize the SQLAlchemy engine
# We set check_same_thread=False for SQLite to allow Panel callbacks from different threads
try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
except Exception as e:
    print(f"Error initializing database engine: {e}")
    raise

# Define the base class for declarative models
Base = declarative_base()

# =========================================================
# DATABASE TABLE
# =========================================================

class SensorData(Base):
    """
    SQLAlchemy ORM model for storing sensor readings.

    Attributes:
        id (int): Primary key for the record.
        sensor (str): The name or key of the sensor (e.g., 'temperature').
        value (float): The recorded numeric value from the sensor.
        timestamp (DateTime): The exact date and time the reading was received.
    """
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True)
    sensor = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# =========================================================
# CREATE TABLES
# =========================================================

try:
    # Creates tables if they do not already exist
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    print("DATABASE CONNECTED")
except SQLAlchemyError as db_err:
    print(f"Database table creation failed: {db_err}")

# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def get_session():
    """
    Creates and returns a new database session.

    Returns:
        Session: A newly instantiated SQLAlchemy session object.
    """
    return Session()

def save_sensor_data(sensor_name: str, value: float) -> bool:
    """
    Saves a single sensor reading to the database.

    Args:
        sensor_name (str): The identifier for the sensor.
        value (float): The measured value to record.

    Returns:
        bool: True if the save was successful, False otherwise.
    """
    local_session = Session()
    try:
        # Create a new record object
        data = SensorData(
            sensor=sensor_name,
            value=value,
            timestamp=datetime.now()
        )
        # Add and commit the record to the database
        local_session.add(data)
        local_session.commit()
        return True
    except SQLAlchemyError as e:
        # Roll back the transaction if an error occurs to prevent partial saves
        local_session.rollback()
        print(f"Database error saving {sensor_name}: {e}")
        return False
    except Exception as e:
        local_session.rollback()
        print(f"Unexpected error saving {sensor_name}: {e}")
        return False
    finally:
        # Ensure the session is always closed to free connection resources
        local_session.close()
