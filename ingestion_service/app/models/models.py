from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Sensor(Base):
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False) # MAC Address
    device_type = Column(String, index=True, nullable=False) # radar, security_camera, access_controller

    events = relationship("Event", back_populates="sensor")


class Event(Base):
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    device_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String, index=True, nullable=False)
    data = Column(JSONB, nullable=True) # Flexible field for specific event data

    sensor = relationship("Sensor", back_populates="events")
