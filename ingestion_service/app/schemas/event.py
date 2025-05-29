from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.common import MACAddress


class EventBase(BaseModel):
    device_id: MACAddress
    timestamp: datetime
    event_type: str


class EventCreate(EventBase):
    # Access control fields
    user_id: Optional[str] = None
    
    # Speed violation fields  
    speed_kmh: Optional[int] = None
    location: Optional[str] = None
    
    # Intrusion detection fields
    zone: Optional[str] = None
    confidence: Optional[float] = None
    photo_base64: Optional[str] = None


class EventCreateInternal(EventBase):
    data: Optional[dict] = None
    sensor_id: int


class EventRead(EventBase):
    id: int
    sensor_id: int
    data: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}
