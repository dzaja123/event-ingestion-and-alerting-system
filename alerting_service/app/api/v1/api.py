from fastapi import APIRouter
from app.api.v1.endpoints import alerts, authorized_users

api_router = APIRouter()

api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(authorized_users.router, prefix="/users", tags=["Users"])
