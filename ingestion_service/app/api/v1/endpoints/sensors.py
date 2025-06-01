from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app import crud, schemas
from app.db.session import get_db
from app.services.cache_service import cache_service
from app.schemas.common import MACAddress

router = APIRouter()


@router.get("/", response_model=List[schemas.sensor.SensorRead])
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


@router.post("/", response_model=schemas.sensor.SensorRead, status_code=status.HTTP_201_CREATED)
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


@router.get("/{device_id}", response_model=schemas.sensor.SensorRead)
async def read_sensor(
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
async def update_sensor(
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
async def patch_sensor(
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
async def delete_sensor(
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
