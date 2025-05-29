from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import uvicorn

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.message_queue_service import message_queue_service
from app.services.cache_service import cache_service
from app.db.session import engine
from app.models.models import Base


# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Ingestion Service starting up...")
    
    # Initialize database schema
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise
    
    try:
        await message_queue_service.connect()
        logger.info("Connected to Message Queue.")
    except Exception as e:
        logger.error(f"Failed to connect to Message Queue on startup: {e}")

    logger.info("Ingestion Service startup complete.")
    yield
    
    # Shutdown
    logger.info("Ingestion Service shutting down...")
    await message_queue_service.close()
    logger.info("Message Queue connection closed.")
    await cache_service.close()
    logger.info("Cache service connection closed.")
    logger.info("Ingestion Service shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    # TODO: Add health checks for DB, Redis, MQ
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
