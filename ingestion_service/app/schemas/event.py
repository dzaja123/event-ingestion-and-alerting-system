from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from app.schemas.common import MACAddress
import base64


class EventBase(BaseModel):
    device_id: MACAddress
    timestamp: datetime
    event_type: str
    
    @field_validator('device_id')
    @classmethod
    def normalize_device_id(cls, v):
        """Normalize MAC address to uppercase."""
        return v.upper() if isinstance(v, str) else v


class EventCreate(EventBase):
    # Access control fields
    user_id: Optional[str] = None
    
    # Speed violation fields  
    speed_kmh: Optional[int] = Field(None, ge=0, le=300, description="Speed in km/h (0-300)")
    location: Optional[str] = None
    
    # Intrusion detection fields
    zone: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level between 0.0 and 1.0")
    photo_base64: Optional[str] = Field(None, description="Base64 encoded photo string")

    @field_validator('photo_base64')
    @classmethod
    def validate_photo_base64(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        try:
            # Attempt to decode the base64 string to validate it
            base64.b64decode(v, validate=True)
            return v
        except Exception:
            raise ValueError("Invalid base64 string for photo_base64")


class EventCreateInternal(EventBase):
    data: Optional[dict] = None
    sensor_id: int


class EventRead(EventBase):
    id: int
    sensor_id: int
    data: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}
