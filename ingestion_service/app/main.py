from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import logging
import uvicorn
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.message_queue_service import message_queue_service
from app.services.cache_service import cache_service
from app.db.session import engine, AsyncSessionLocal
from app.models.models import Base
from app.core.seeder import ingestion_seeder


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

    # Seed database if enabled
    if settings.ENABLE_SEEDING:
        try:
            async with AsyncSessionLocal() as db:
                await ingestion_seeder.seed_all(db)
            logger.info("Database seeding completed.")
        except Exception as e:
            logger.error(f"Failed to seed database: {e}")

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
    """Health check endpoint with dependency verification"""
    health_status = {
        "status": "healthy",
        "service": "ingestion_service",
        "dependencies": {}
    }
    
    # Check database
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        await cache_service.redis_client.ping()
        health_status["dependencies"]["redis"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check RabbitMQ
    try:
        if message_queue_service.connection and not message_queue_service.connection.is_closed:
            health_status["dependencies"]["rabbitmq"] = "healthy"
        else:
            health_status["dependencies"]["rabbitmq"] = "unhealthy: connection not established"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["dependencies"]["rabbitmq"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
