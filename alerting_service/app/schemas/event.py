from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class EventReceived(BaseModel):
    """Schema for events received from RabbitMQ"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    device_id: str
    sensor_id: int
    timestamp: datetime
    event_type: str
    data: Optional[Dict[str, Any]] = None
    created_at: datetime