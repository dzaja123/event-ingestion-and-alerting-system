from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
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
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String, index=True, nullable=False)
    data = Column(JSON, nullable=True)

    sensor = relationship("Sensor", back_populates="events")

    @property
    def device_id(self) -> str:
        """Get device_id via sensor relationship for backward compatibility."""
        return self.sensor.device_id if self.sensor else ""
