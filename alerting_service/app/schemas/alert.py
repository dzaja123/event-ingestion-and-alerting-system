from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class AlertBase(BaseModel):
    device_id: str  # MAC address from event
    alert_type: Literal["unauthorized_access", "speed_violation", "intrusion_detection"] = Field(
        ..., 
        description="Type of alert generated"
    )
    timestamp: datetime


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