from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models.models import Alert
from app.schemas.alert import AlertCreate, AlertRead, AlertFilter
from typing import List, Optional
from datetime import datetime


class CRUDAlert:
    async def create(self, db: AsyncSession, *, obj_in: AlertCreate) -> Alert:
        db_obj = Alert(
            event_id=obj_in.event_id,
            device_id=obj_in.device_id,
            alert_type=obj_in.alert_type,
            timestamp=obj_in.timestamp,
            photo_base64=obj_in.photo_base64
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
        filters: Optional[AlertFilter] = None
    ) -> List[AlertRead]:
        query = select(Alert).order_by(Alert.timestamp.desc())

        if filters:
            if filters.alert_type:
                query = query.filter(Alert.alert_type == filters.alert_type)
            if filters.device_id:
                query = query.filter(Alert.device_id == filters.device_id)
            if filters.start_time:
                query = query.filter(Alert.timestamp >= filters.start_time)
            if filters.end_time:
                query = query.filter(Alert.timestamp <= filters.end_time)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        alerts = result.scalars().all()
        return [AlertRead.model_validate(alert) for alert in alerts]

    async def get_by_id(self, db: AsyncSession, *, alert_id: int) -> Optional[Alert]:
        result = await db.execute(select(Alert).filter(Alert.id == alert_id))
        return result.scalars().first()


alert = CRUDAlert() 