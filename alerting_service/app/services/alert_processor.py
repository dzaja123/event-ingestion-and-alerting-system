from app.schemas.event import EventReceived
from app.schemas.alert import AlertCreate
from app.core.config import settings
from app.services.cache_service import cache_service
from app import crud
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AlertProcessor:
    def __init__(self):
        pass

    async def process_event(self, event: EventReceived, db: AsyncSession) -> Optional[AlertCreate]:
        """
        Process an event and determine if an alert should be generated.
        Returns AlertCreate object if alert should be created, None otherwise.
        """
        try:
            if event.event_type == "access_attempt":
                return await self._process_access_control_event(event, db)
            elif event.event_type == "speed_violation":
                return await self._process_radar_speed_event(event, db)
            elif event.event_type == "motion_detected":
                return await self._process_intrusion_detection_event(event, db)
            else:
                logger.warning(f"Unknown event type: {event.event_type}")
                return None
        except Exception as e:
            logger.error(f"Error processing event {event.id}: {e}")
            return None

    async def _process_access_control_event(self, event: EventReceived, db: AsyncSession) -> Optional[AlertCreate]:
        """Process access control events for unauthorized access"""
        if not event.data or "user_id" not in event.data:
            logger.warning(f"Access control event {event.id} missing user_id")
            return None

        user_id = event.data["user_id"]

        # Check cache first
        is_authorized_cached = await cache_service.is_user_authorized(user_id)
        
        if is_authorized_cached:
            # User is authorized, no alert needed
            return None

        # Check database if not in cache
        is_authorized_db = await crud.authorized_user.is_user_authorized(db, user_id=user_id)
        
        if is_authorized_db:
            # User is authorized but not cached, add to cache
            await cache_service.add_authorized_user(user_id)
            return None

        # User is not authorized, create alert
        return AlertCreate(
            event_id=event.id,
            device_id=event.device_id,
            alert_type="unauthorized_access",
            timestamp=event.timestamp
        )

    async def _process_radar_speed_event(self, event: EventReceived, db: AsyncSession) -> Optional[AlertCreate]:
        """Process radar speed events for speed violations"""
        if not event.data or "speed_kmh" not in event.data:
            logger.warning(f"Radar speed event {event.id} missing speed_kmh")
            return None

        speed_kmh = event.data.get("speed_kmh")
        
        if not isinstance(speed_kmh, (int, float)) or speed_kmh <= settings.SPEED_VIOLATION_THRESHOLD:
            # Speed is within limits, no alert needed
            return None

        # Speed violation detected
        return AlertCreate(
            event_id=event.id,
            device_id=event.device_id,
            alert_type="speed_violation",
            timestamp=event.timestamp
        )

    async def _process_intrusion_detection_event(self, event: EventReceived, db: AsyncSession) -> Optional[AlertCreate]:
        """Process intrusion detection events for restricted areas"""
        if not event.data or "zone" not in event.data:
            logger.warning(f"Intrusion detection event {event.id} missing zone")
            return None

        zone = event.data.get("zone")
        
        # Check if it's a restricted area
        if not self._is_restricted_area(zone):
            return None

        # Check if it's after hours
        if not self._is_after_hours(event.timestamp):
            return None

        photo_base64 = event.data.get("photo_base64")

        if not photo_base64:
            logger.warning(f"Intrusion detection event {event.id} missing photo_base64")
            return None

        return AlertCreate(
            event_id=event.id,
            device_id=event.device_id,
            alert_type="intrusion_detection",
            timestamp=event.timestamp,
            photo_base64=photo_base64
        )

    def _is_restricted_area(self, zone: str) -> bool:
        """Determine if the zone is restricted"""
        restricted_zones = ["Restricted Area", "Secure Zone", "Private Area", "Classified Zone"]
        return any(restricted in zone for restricted in restricted_zones)

    def _is_after_hours(self, timestamp: datetime) -> bool:
        """Determine if the event occurred after hours"""
        hour = timestamp.hour
        return hour >= 18 or hour < 6


alert_processor = AlertProcessor()
