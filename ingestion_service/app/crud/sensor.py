from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import List, Optional
from app.models.models import Sensor
from app.schemas.sensor import SensorCreate, SensorUpdate


class CRUDSensor:
    async def get_by_device_id(self, db: AsyncSession, *, device_id: str) -> Sensor | None:
        result = await db.execute(
            select(Sensor).filter(Sensor.device_id == device_id)
        )
        return result.scalars().first()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        device_type: Optional[str] = None
    ) -> List[Sensor]:
        """
        Retrieve multiple sensors with optional filtering by device_type
        """
        query = select(Sensor)
        
        if device_type:
            query = query.filter(Sensor.device_type == device_type)
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: SensorCreate) -> Sensor:
        db_obj = Sensor(
            device_id=obj_in.device_id,
            device_type=obj_in.device_type
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_by_device_id(
        self, 
        db: AsyncSession, 
        *, 
        device_id: str, 
        obj_in: SensorUpdate
    ) -> Sensor | None:
        """Update sensor by device_id"""
        # First check if sensor exists
        existing_sensor = await self.get_by_device_id(db, device_id=device_id)
        if not existing_sensor:
            return None

        # Only update if device_type is provided
        if obj_in.device_type is not None:
            await db.execute(
                update(Sensor)
                .where(Sensor.device_id == device_id)
                .values(device_type=obj_in.device_type)
            )
            await db.commit()
            await db.refresh(existing_sensor)

        return existing_sensor

    async def delete_by_device_id(self, db: AsyncSession, *, device_id: str) -> bool:
        """Permanently delete sensor"""
        result = await db.execute(
            delete(Sensor).where(Sensor.device_id == device_id)
        )
        await db.commit()
        return result.rowcount > 0


sensor = CRUDSensor()
