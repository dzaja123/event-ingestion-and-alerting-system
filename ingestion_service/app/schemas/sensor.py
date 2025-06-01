from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.common import MACAddress
from app.domain.sensor_types import DeviceType


class SensorBase(BaseModel):
    device_id: MACAddress
    device_type: DeviceType = Field(
        description="Type of IoT sensor device"
    )

    @field_validator('device_id')
    @classmethod
    def normalize_device_id(cls, v):
        return v.upper()


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    """Schema for updating sensor details - only device_type can be updated"""
    device_type: Optional[DeviceType] = Field(
        None, description="Type of IoT sensor device"
    )


class SensorInDB(SensorBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class SensorRead(SensorInDB):
    pass