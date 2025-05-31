from sqlalchemy import Column, String, Integer, DateTime, Text
from app.db.base_class import Base


class AuthorizedUser(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)


class Alert(Base):
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, nullable=True, index=True)  # Reference to original event
    device_id = Column(String, index=True, nullable=False)
    alert_type = Column(String, index=True, nullable=False)  # unauthorized_access, speed_violation, intrusion_detection
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    photo_base64 = Column(Text, nullable=True)  # Base64 encoded photo for intrusion detection alerts 