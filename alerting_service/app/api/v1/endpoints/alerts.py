from fastapi import APIRouter, Depends, Query, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import ValidationError

from app import crud
from app.db.session import get_db
from app.schemas.alert import AlertRead, AlertFilter

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=List[AlertRead])
@limiter.limit("100/minute")
async def get_alerts(
    request: Request,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    start_time: Optional[datetime] = Query(None, description="Filter alerts from this timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter alerts up to this timestamp")
):
    """
    Retrieve triggered alerts with optional filters.
    
    Available alert types:
    - unauthorized_access
    - speed_violation  
    - intrusion_detection
    """
    try:
        filters = AlertFilter(
            alert_type=alert_type,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter parameters: {e.errors()[0]['msg']} for field '{e.errors()[0]['loc'][0]}'"
        )
    
    alerts = await crud.alert.get_multi(
        db,
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    return alerts


@router.get("/{alert_id}", response_model=AlertRead)
@limiter.limit("200/minute")
async def get_alert_by_id(
    request: Request,
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert by ID"""
    alert = await crud.alert.get_by_id(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return AlertRead.model_validate(alert) 