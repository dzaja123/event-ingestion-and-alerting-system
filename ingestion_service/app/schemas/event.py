from pydantic import BaseModel, Field, field_validator, RootModel, model_validator
from datetime import datetime
from typing import Optional, Union, Literal
from app.schemas.common import MACAddress
import base64


class EventBase(BaseModel):
    device_id: MACAddress
    timestamp: datetime
    
    @field_validator('device_id')
    @classmethod
    def normalize_device_id(cls, v):
        """Normalize MAC address to uppercase."""
        return v.upper() if isinstance(v, str) else v


class AccessControlEvent(EventBase):
    event_type: Literal["access_attempt"] = "access_attempt"
    user_id: str = Field(..., description="User ID attempting access")


class RadarSpeedEvent(EventBase):
    event_type: Literal["speed_violation"] = "speed_violation"
    speed_kmh: int = Field(..., ge=0, le=300, description="Speed in km/h (0-300)")
    location: str = Field(..., description="Location where speed was detected")


class IntrusionDetectionEvent(EventBase):
    event_type: Literal["motion_detected"] = "motion_detected"
    zone: str = Field(..., description="Zone where motion was detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level between 0.0 and 1.0")
    photo_base64: str = Field(..., description="Base64 encoded photo string")

    @field_validator('photo_base64')
    @classmethod
    def validate_photo_base64(cls, v: str) -> str:
        try:
            # Attempt to decode the base64 string to validate it
            base64.b64decode(v, validate=True)
            return v
        except Exception:
            raise ValueError("Invalid base64 string for photo_base64")


class EventCreate(RootModel[Union[AccessControlEvent, RadarSpeedEvent, IntrusionDetectionEvent]]):
    root: Union[AccessControlEvent, RadarSpeedEvent, IntrusionDetectionEvent] = Field(discriminator='event_type')

    @model_validator(mode='before')
    @classmethod
    def validate_strict_fields(cls, data):
        """Ensure only the fields belonging to the specific event type are present"""
        if not isinstance(data, dict):
            return data

        event_type = data.get('event_type')
        
        # Use validation service to avoid circular imports
        from app.services.validation_service import validation_service
        
        provided_fields = set(data.keys())
        is_valid, extra_fields = validation_service.validate_event_fields(event_type, provided_fields)
        
        if not is_valid:
            if not event_type or not validation_service.domain.is_valid_event_type(event_type):
                raise ValueError(f"Unknown event_type: {event_type}")
            
            if extra_fields:
                raise ValueError(f"Extra fields not allowed for event_type '{event_type}': {', '.join(extra_fields)}")

        return data

    def __getattr__(self, name):
        return getattr(self.root, name)


class EventCreateInternal(BaseModel):
    timestamp: datetime
    event_type: str
    data: Optional[dict] = None
    sensor_id: int


class EventRead(BaseModel):
    id: int
    device_id: str
    timestamp: datetime
    sensor_id: int
    event_type: str
    data: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}
