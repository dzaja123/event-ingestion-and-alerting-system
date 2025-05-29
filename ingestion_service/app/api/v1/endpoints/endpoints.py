from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app import crud, schemas
from app.db.session import get_db
from app.services.cache_service import cache_service
from app.services.message_queue_service import message_queue_service
from app.schemas.common import MACAddress
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
    - Stores event in PostgreSQL.
    - Publishes event to RabbitMQ.
    """

    sensor_details_cached = await cache_service.get_sensor_details(event_in.device_id)
    
    if sensor_details_cached:
        db_sensor_data = sensor_details_cached
    else:
        db_sensor_from_db = await crud.sensor.get_by_device_id(db, device_id=event_in.device_id)
        if not db_sensor_from_db:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Device ID '{event_in.device_id}' is not registered. Payloads from unregistered sensors are restricted."
            )
        db_sensor_data = schemas.sensor.SensorRead.model_validate(db_sensor_from_db)
        await cache_service.set_sensor_details(db_sensor_data)

    event_create_internal = schemas.event.EventCreateInternal(
        device_id=event_in.device_id,
        timestamp=event_in.timestamp,
        event_type=event_in.event_type,
        data=event_in.model_dump(exclude={'device_id', 'timestamp', 'event_type'}),
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


@router.get("/sensors/", response_model=List[schemas.sensor.SensorRead], tags=["Sensors (Admin)"])
async def read_sensors(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    device_type: Optional[str] = Query(None, description="Filter by device type")
):
    """
    Retrieve all registered sensors with optional pagination and device type filter.
    """
    sensors = await crud.sensor.get_multi(
        db,
        skip=skip,
        limit=limit,
        device_type=device_type
    )
    return sensors


@router.post("/sensors/", response_model=schemas.sensor.SensorRead, status_code=status.HTTP_201_CREATED, tags=["Sensors (Admin)"])
async def create_sensor(
    *,
    db: AsyncSession = Depends(get_db),
    sensor_in: schemas.sensor.SensorCreate
):
    """
    Register a new sensor
    """
    existing_sensor = await crud.sensor.get_by_device_id(db, device_id=sensor_in.device_id)
    if existing_sensor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor with device ID '{sensor_in.device_id}' already exists."
        )
    sensor = await crud.sensor.create(db=db, obj_in=sensor_in)
    # Cache registered sensor details
    sensor_read = schemas.sensor.SensorRead.model_validate(sensor)
    await cache_service.set_sensor_details(sensor_read)
    return sensor_read


@router.get("/sensors/{device_id}", response_model=schemas.sensor.SensorRead, tags=["Sensors (Admin)"])
async def read_sensor(
    device_id: MACAddress,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a sensor by its device ID.
    """
    sensor = await crud.sensor.get_by_device_id(db, device_id=device_id)
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    return sensor

