from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class EventReceived(BaseModel):
    """Schema for events received from RabbitMQ"""
    id: int
    device_id: str
    sensor_id: int
    timestamp: datetime
    event_type: str
    data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True 