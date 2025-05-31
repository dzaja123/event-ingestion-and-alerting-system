from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


def validate_mac_address(value: str) -> str:
    """Validate MAC address format and normalize to uppercase"""
    pattern = r'^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$'
    if not re.match(pattern, value):
        raise ValueError('Invalid MAC address format. Expected format: XX:XX:XX:XX:XX:XX')
    return value.upper()


class AlertBase(BaseModel):
    device_id: str = Field(..., description="MAC address from event")
    alert_type: Literal["unauthorized_access", "speed_violation", "intrusion_detection"] = Field(
        ..., 
        description="Type of alert generated"
    )
    timestamp: datetime

    @field_validator('device_id')
    @classmethod
    def validate_device_id(cls, v):
        return validate_mac_address(v)


class AlertCreate(AlertBase):
    event_id: Optional[int] = None


class AlertRead(AlertBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_id: Optional[int] = None
    created_at: datetime


class AlertFilter(BaseModel):
    alert_type: Optional[Literal["unauthorized_access", "speed_violation", "intrusion_detection"]] = None
    device_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None