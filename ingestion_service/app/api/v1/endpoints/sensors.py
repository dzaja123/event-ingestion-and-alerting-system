from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app import crud, schemas
from app.db.session import get_db
from app.services.cache_service import cache_service
from app.schemas.common import MACAddress

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=List[schemas.sensor.SensorRead])
@limiter.limit("100/minute")
async def read_sensors(
    request: Request,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
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


@router.post("/", response_model=schemas.sensor.SensorRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_sensor(
    request: Request,
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


@router.get("/{device_id}", response_model=schemas.sensor.SensorRead)
@limiter.limit("200/minute")
async def read_sensor(
    request: Request,
    device_id: MACAddress,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a sensor by its device ID
    """
    sensor = await crud.sensor.get_by_device_id(db, device_id=device_id)
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    return sensor


@router.put("/{device_id}", response_model=schemas.sensor.SensorRead)
@limiter.limit("20/minute")
async def update_sensor(
    request: Request,
    device_id: MACAddress,
    sensor_update: schemas.sensor.SensorUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update sensor details (device_type only)
    """
    sensor = await crud.sensor.update_by_device_id(db, device_id=device_id, obj_in=sensor_update)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Sensor not found or inactive"
        )

    # Invalidate cache and update with new data
    await cache_service.delete_sensor_details(device_id)
    sensor_read = schemas.sensor.SensorRead.model_validate(sensor)
    await cache_service.set_sensor_details(sensor_read)
    
    return sensor_read


@router.patch("/{device_id}", response_model=schemas.sensor.SensorRead)
@limiter.limit("20/minute")
async def patch_sensor(
    request: Request,
    device_id: MACAddress,
    sensor_update: schemas.sensor.SensorUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Patch sensor details
    """
    sensor = await crud.sensor.update_by_device_id(db, device_id=device_id, obj_in=sensor_update)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Sensor not found or inactive"
        )

    # Invalidate cache and update with new data
    await cache_service.delete_sensor_details(device_id)
    sensor_read = schemas.sensor.SensorRead.model_validate(sensor)
    await cache_service.set_sensor_details(sensor_read)
    
    return sensor_read


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_sensor(
    request: Request,
    device_id: MACAddress,
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete sensor and remove from cache
    """
    success = await crud.sensor.delete_by_device_id(db, device_id=device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Sensor not found"
        )

    # Remove from cache
    await cache_service.delete_sensor_details(device_id)
