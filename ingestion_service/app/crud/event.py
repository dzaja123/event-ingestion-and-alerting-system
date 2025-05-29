from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Event, Sensor
from app.schemas.event import EventCreateInternal, EventRead
from typing import List, Optional
from datetime import datetime


class CRUDEvent:
    async def create(self, db: AsyncSession, *, obj_in: EventCreateInternal) -> Event:
        db_obj = Event(
            sensor_id=obj_in.sensor_id,
            device_id=obj_in.device_id,
            timestamp=obj_in.timestamp,
            event_type=obj_in.event_type,
            data=obj_in.data if obj_in.data else {}
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        device_type: Optional[str] = None # This requires a join with Sensor
    ) -> List[EventRead]:
        query = select(Event).order_by(Event.timestamp.desc())

        if start_time:
            query = query.filter(Event.timestamp >= start_time)
        if end_time:
            query = query.filter(Event.timestamp <= end_time)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        if device_type:
            query = query.join(Sensor).filter(Sensor.device_type == device_type)
            
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        events = result.scalars().all()
        return [EventRead.model_validate(event) for event in events]


event = CRUDEvent()
