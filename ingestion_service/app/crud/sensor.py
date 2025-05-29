from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.models import Sensor
from app.schemas.sensor import SensorCreate


class CRUDSensor:
    async def get_by_device_id(self, db: AsyncSession, *, device_id: str) -> Sensor | None:
        result = await db.execute(select(Sensor).filter(Sensor.device_id == device_id))
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


sensor = CRUDSensor()
