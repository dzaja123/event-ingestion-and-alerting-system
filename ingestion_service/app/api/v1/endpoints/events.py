from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app import crud, schemas
from app.db.session import get_db
from app.services.cache_service import cache_service
from app.services.message_queue_service import message_queue_service
from app.services.validation_service import validation_service
from app.schemas.event import EventCreate, EventRead

router = APIRouter()


@router.post("/", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    *,
    db: AsyncSession = Depends(get_db),
    event_in: EventCreate
):
    """
    Accept IoT event data.
    - Validates `device_id` as a valid MAC address.
    - Checks if sensor is registered.
    - Validates event type matches sensor device type.
    - Stores event in PostgreSQL.
    - Publishes event to RabbitMQ.
    """

    sensor_details_cached = await cache_service.get_sensor_details(event_in.root.device_id)
    
    if sensor_details_cached:
        db_sensor_data = sensor_details_cached
    else:
        db_sensor_from_db = await crud.sensor.get_by_device_id(db, device_id=event_in.root.device_id)
        if not db_sensor_from_db:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Device ID '{event_in.root.device_id}' is not registered. Payloads from unregistered sensors are restricted."
            )
        db_sensor_data = schemas.sensor.SensorRead.model_validate(db_sensor_from_db)
        await cache_service.set_sensor_details(db_sensor_data)

    # Validate event type matches sensor device type using validation service
    if not validation_service.validate_device_event_combination(
        db_sensor_data.device_type.value, 
        event_in.root.event_type
    ):
        error_message = validation_service.get_validation_error_message(
            db_sensor_data.device_type.value, 
            event_in.root.event_type
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    event_create_internal = schemas.event.EventCreateInternal(
        device_id=event_in.root.device_id,
        timestamp=event_in.root.timestamp,
        event_type=event_in.root.event_type,
        data=event_in.root.model_dump(exclude={'device_id', 'timestamp', 'event_type'}),
        sensor_id=db_sensor_data.id
    )
    
    created_event_db = await crud.event.create(db=db, obj_in=event_create_internal)
    
    # Convert DB model to Pydantic Read schema for response and MQ
    event_out = schemas.event.EventRead.model_validate(created_event_db)

    try:
        await message_queue_service.publish_event(event_out)
    except ConnectionError as e:
        print(f"Warning: Failed to publish event to RabbitMQ: {e}")
    except Exception as e:
        print(f"Error during MQ publish: {e}")

    return event_out


@router.get("/", response_model=List[schemas.event.EventRead])
async def read_events(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_time: Optional[datetime] = Query(None, description="Filter events from this timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter events up to this timestamp"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    device_type: Optional[str] = Query(None, description="Filter by device type")
):
    """
    Retrieve stored events with optional filters for time range, event type, or device type.
    """
    events = await crud.event.get_multi(
        db, 
        skip=skip, 
        limit=limit, 
        start_time=start_time, 
        end_time=end_time, 
        event_type=event_type,
        device_type=device_type
    )
    return events

