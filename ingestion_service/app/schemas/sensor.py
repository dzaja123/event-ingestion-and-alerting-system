from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal
from app.schemas.common import MACAddress


class SensorBase(BaseModel):
    device_id: MACAddress
    device_type: Literal["radar", "security_camera", "access_controller"] = Field(
        ..., 
        description="Type of IoT sensor device"
    )
    
    @field_validator('device_id')
    @classmethod
    def normalize_device_id(cls, v):
        """Normalize MAC address to uppercase."""
        return v.upper() if isinstance(v, str) else v


class SensorCreate(SensorBase):
    pass


class SensorInDB(SensorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SensorRead(SensorInDB):
    pass