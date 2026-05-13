# =========================================================
# DATABASE MODULE
# =========================================================

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

# =========================================================
# DATABASE SETUP
# =========================================================

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

Base = declarative_base()

# =========================================================
# DATABASE TABLE
# =========================================================

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True)
    sensor = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime)

# =========================================================
# CREATE TABLES
# =========================================================

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

print("DATABASE CONNECTED")

# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def get_session():
    return Session()

def save_sensor_data(sensor_name, value):
    local_session = Session()
    try:
        from datetime import datetime
        data = SensorData(
            sensor=sensor_name,
            value=value,
            timestamp=datetime.now()
        )
        local_session.add(data)
        local_session.commit()
    finally:
        local_session.close()
