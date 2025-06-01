import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.db.session import get_db
from app.models.models import Base
from app.services.cache_service import cache_service
from app.services.message_queue_service import message_queue_service
from app.models.models import Sensor, Event
from app.schemas.sensor import SensorCreate
from app.schemas.event import EventCreate
from datetime import datetime, timezone


# Test database URL, in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # In-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    
    # Create all tables
    from app.db.base_class import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def mock_cache_service():
    """Create a mock cache service."""
    cache_service.get_sensor_details = AsyncMock(return_value=None)
    cache_service.set_sensor_details = AsyncMock()
    cache_service.delete_sensor_details = AsyncMock()
    cache_service.get_event_data = AsyncMock(return_value=None)
    cache_service.set_event_data = AsyncMock()
    return cache_service


@pytest.fixture
def mock_message_queue():
    """Create a mock message queue service."""
    message_queue_service.publish_event = AsyncMock()
    return message_queue_service


@pytest.fixture
async def client(db_session: AsyncSession, mock_cache_service, mock_message_queue) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with dependency overrides."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_sensor(db_session: AsyncSession) -> Sensor:
    """Create a sample sensor for testing."""
    sensor = Sensor(
        device_id="AA:BB:CC:DD:EE:FF",
        device_type="access_controller"
    )
    db_session.add(sensor)
    await db_session.commit()
    await db_session.refresh(sensor)
    return sensor


@pytest.fixture
async def sample_event(db_session: AsyncSession, sample_sensor: Sensor) -> Event:
    """Create a sample event for testing."""
    event = Event(
        device_id=sample_sensor.device_id,
        event_type="temperature_reading",
        data={"temperature": 25.5, "humidity": 60.0},
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    return event


@pytest.fixture
def sample_sensor_data():
    """Sample sensor data for testing."""
    return {
        "device_id": "AA:BB:CC:DD:EE:FF",
        "device_type": "access_controller"
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "device_id": "AA:BB:CC:DD:EE:FF",
        "event_type": "access_attempt",
        "timestamp": "2024-12-18T14:00:00Z",
        "user_id": "user123"
    }


@pytest.fixture
def sample_speed_event_data():
    """Sample speed violation event data for testing."""
    return {
        "device_id": "11:22:33:44:55:66",
        "timestamp": "2024-12-18T14:00:00Z",
        "event_type": "speed_violation",
        "speed_kmh": 120,
        "location": "Zone A"
    }


@pytest.fixture
def sample_intrusion_event_data():
    """Sample intrusion detection event data for testing."""
    return {
        "device_id": "77:88:99:AA:BB:CC",
        "timestamp": "2024-12-18T22:00:00Z",
        "event_type": "motion_detected",
        "zone": "Restricted Area",
        "confidence": 0.95,
        "photo_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    } 