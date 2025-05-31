from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal
import re


MAC_ADDRESS_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$")


def validate_mac_address(value: str) -> str:
    """Validate and normalize MAC address to uppercase colon-separated format."""
    if not isinstance(value, str) or not value:
        raise ValueError("MAC address must be a non-empty string")
    if not MAC_ADDRESS_REGEX.match(value):
        raise ValueError("Invalid MAC address format. Expected format: XX:XX:XX:XX:XX:XX")
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
        """Validate MAC address format."""
        return validate_mac_address(v)


class AlertCreate(AlertBase):
    event_id: Optional[int] = None


class AlertRead(AlertBase):
    id: int
    event_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertFilter(BaseModel):
    alert_type: Optional[Literal["unauthorized_access", "speed_violation", "intrusion_detection"]] = None
    device_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None 