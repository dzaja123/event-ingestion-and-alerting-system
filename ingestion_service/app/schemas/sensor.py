from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.common import MACAddress


class SensorBase(BaseModel):
    device_id: MACAddress
    device_type: str = Field(..., examples=["radar", "security_camera", "access_controller"])


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