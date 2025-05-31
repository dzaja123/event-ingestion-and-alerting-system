from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.common import MACAddress


class SensorBase(BaseModel):
    device_id: MACAddress
    device_type: Literal["radar", "security_camera", "access_controller"] = Field(
        description="Type of IoT sensor device"
    )

    @field_validator('device_id')
    @classmethod
    def normalize_device_id(cls, v):
        return v.upper()


class SensorCreate(SensorBase):
    pass


class SensorInDB(SensorBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class SensorRead(SensorInDB):
    pass