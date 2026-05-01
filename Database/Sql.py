import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import time

# Base class — our table class inherits from this
Base = declarative_base()

class SensorReading(Base):
    """
    One row = one timestamped set of sensor measurements.
    """
    __tablename__ = 'sensor_readings'

    id          = Column(Integer, primary_key=True, autoincrement=True)
    timestamp   = Column(DateTime, nullable=False, default=datetime.now)
    soil_moisture = Column(Float, nullable=True)
    temperature = Column(Float, nullable=False)
    humidity    = Column(Float, nullable=False)
    water_level = Column(Float, nullable=True)
    ambient_light = Column(Float, nullable=False)
    rainfall    = Column(Float, nullable=True)
    motion_detection = Column(Float, nullable=True)
    ultrasonic_distance = Column(Float, nullable=True)
    pump_status = Column(Float, nullable=True)
    fan_status = Column(Float, nullable=True)

    def __repr__(self):
        return (f"<Reading {self.timestamp:%Y-%m-%d %H:%M} | "
                f"T={self.temperature}°C, H={self.humidity}%RH, L={self.ambient_light} lux>," 
                f"K={self.soil_moisture}%, W={self.water_level}%, R={self.rainfall}mm,"
                f"M={self.motion_detection}, U={self.ultrasonic_distance}cm, P={self.pump_status}," 
                f"F={self.fan_status}>")

engine = create_engine('sqlite:///sensor_data.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

for i in range(10):
    reading = SensorReading(
        timestamp=datetime(2025, 6, 1, 8, i, 0),
        temperature=20.0 + i,
        humidity=60.0 + i,
        ambient_light=10000.0 + (i * 1000),
        soil_moisture=40.0 + (i * 2),
        water_level=70.0 + (i * 3),
        rainfall=(5.0 + (i * 0.5)) if i % 2 == 0 else 0.0,
        motion_detection=0.0,
        ultrasonic_distance=150.0 - (i * 5),
        pump_status=0.0,
        fan_status=0.0
        #steam_status=
    )
    session.add(reading)

session.commit()

hot = (
    session.query(SensorReading)
    .filter(SensorReading.temperature > 24.0)
    .order_by(SensorReading.timestamp)
    .all()
)

stats = session.query(
    func.min(SensorReading.temperature).label('temp_min'),
    func.avg(SensorReading.temperature).label('temp_avg'),
    func.max(SensorReading.temperature).label('temp_max'),
    func.min(SensorReading.humidity).label('humid_min'),
    func.avg(SensorReading.humidity).label('humid_avg'),
    func.max(SensorReading.humidity).label('humid_max'),
    func.min(SensorReading.ambient_light).label('light_min'),
    func.avg(SensorReading.ambient_light).label('light_avg'),
    func.max(SensorReading.ambient_light).label('light_max'),
).one()

print(f"Temperature: min={stats.temp_min:.1f}°C, avg={stats.temp_avg:.1f}°C, max={stats.temp_max:.1f}°C")
print(f"Humidity: min={stats.humid_min:.1f}%RH, avg={stats.humid_avg:.1f}%RH, max={stats.humid_max:.1f}%RH")
print(f"Ambient Light: min={stats.light_min:.1f} lux, avg={ stats.light_avg:.1f} lux, max={stats.light_max:.1f} lux")   

session.query(SensorReading)

