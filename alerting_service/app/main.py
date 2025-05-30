from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import logging
import uvicorn

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.rabbitmq_consumer import rabbitmq_consumer
from app.services.cache_service import cache_service
from app.db.session import engine
from app.models.models import Base

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Alerting Service starting up...")
    
    # Initialize database schema
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise
    
    try:
        # Initialize authorized users cache
        await rabbitmq_consumer.initialize_authorized_users_cache()
        
        # Start RabbitMQ consumer in the background
        consumer_task = asyncio.create_task(rabbitmq_consumer.start_consuming())
        logger.info("RabbitMQ consumer started")
        
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        raise
    
    logger.info("Alerting Service startup complete.")
    
    yield
    
    # Shutdown
    logger.info("Alerting Service shutting down...")
    
    # Stop RabbitMQ consumer
    await rabbitmq_consumer.stop_consuming()
    
    # Close cache service
    await cache_service.close()
    
    # Cancel consumer task
    if 'consumer_task' in locals() and not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Alerting Service shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    #TODO: Add real health check
    return {
        "status": "healthy",
        "service": "alerting_service",
        "consuming": rabbitmq_consumer.consuming
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 