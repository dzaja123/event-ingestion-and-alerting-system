from pydantic import BaseModel, Field, field_validator, RootModel, model_validator
from pydantic_core import PydanticCustomError
from datetime import datetime
from typing import Optional, Union, Literal
from app.schemas.common import MACAddress
import base64
import binascii
import re


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
    
    @field_validator('speed_kmh', mode='before')
    @classmethod
    def validate_speed_strict(cls, v):
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError("speed_kmh must be an integer, not a string")
        return v


class IntrusionDetectionEvent(EventBase):
    event_type: Literal["motion_detected"] = "motion_detected"
    zone: str = Field(..., description="Zone where motion was detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level between 0.0 and 1.0")
    photo_base64: str = Field(..., description="Base64 encoded photo string")

    @field_validator('confidence', mode='before')
    @classmethod
    def validate_confidence_strict(cls, v):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise ValueError("confidence must be a number (int or float), not a string")
        return v

    @field_validator('photo_base64', mode='before')
    @classmethod
    def validate_photo_base64(cls, v: str) -> str:
        # Check minimum length
        # I found on Google that a valid image is at least 37 characters, but I am not sure if this is correct
        if len(v) < 37:
            raise ValueError("photo_base64 is too short to be a valid image")

        # Check for valid base64 characters only
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', v):
            raise ValueError("photo_base64 contains invalid characters for base64 encoding")

        # Check proper base64 padding
        if len(v) % 4 != 0:
            raise ValueError("photo_base64 has invalid length (must be multiple of 4)")

        try:
            # Attempt to decode the base64 string to validate it
            decoded_data = base64.b64decode(v, validate=True)

            # Check if decoded data looks like an image
            image_headers = [
                b'\xFF\xD8\xFF',  # JPEG
                b'\x89PNG\r\n\x1a\n',  # PNG
                b'GIF87a',  # GIF87a
                b'GIF89a',  # GIF89a
                b'\x42\x4D',  # BMP
                b'RIFF',  # WebP (starts with RIFF)
            ]

            if not any(decoded_data.startswith(header) for header in image_headers):
                raise ValueError("photo_base64 does not contain a valid image format")

            # Check size in MB
            # Threshold at 5MB
            size_mb = len(decoded_data) / (1024 * 1024)
            max_size_mb = 5.0

            if size_mb > max_size_mb:
                raise ValueError(f"Image size {size_mb:.2f}MB exceeds maximum allowed size of {max_size_mb}MB")

            return v
        except binascii.Error:
            raise ValueError("Invalid base64 string for photo_base64")
        except Exception as e:
            if any(msg in str(e) for msg in ["Image size", "photo_base64", "too short", "invalid"]):
                raise e
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
                raise PydanticCustomError(
                    'unknown_event_type',
                    f"Unknown event_type: {event_type}",
                    {'event_type': event_type}
                )
            
            if extra_fields:
                raise PydanticCustomError(
                    'extra_fields_not_allowed',
                    f"Extra fields not allowed for event_type '{event_type}': {', '.join(extra_fields)}",
                    {'extra_fields': list(extra_fields), 'event_type': event_type}
                )

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
