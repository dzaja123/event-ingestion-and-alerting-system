import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock
from datetime import datetime

from app.main import app
from app.db.session import get_db
from app.models.models import Base
from app.services.cache_service import cache_service
from app.schemas.event import EventReceived
from app.schemas.alert import AlertCreate


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
    """Create a clean database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def mock_cache_service():
    """Mock the cache service for testing."""
    original_methods = {}
    
    # Store original methods
    original_methods['is_user_authorized'] = cache_service.is_user_authorized
    original_methods['add_authorized_user'] = cache_service.add_authorized_user
    
    # Mock methods
    cache_service.is_user_authorized = AsyncMock(return_value=False)
    cache_service.add_authorized_user = AsyncMock()
    
    yield cache_service
    
    # Restore original methods
    for method_name, original_method in original_methods.items():
        setattr(cache_service, method_name, original_method)


@pytest.fixture
async def client(db_session: AsyncSession, mock_cache_service) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with dependency overrides."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_access_event():
    """Sample access control event for testing."""
    return EventReceived(
        id=1,
        device_id="AA:BB:CC:DD:EE:FF",
        timestamp=datetime(2024, 12, 18, 14, 0, 0),
        event_type="access_attempt",
        sensor_id=1,
        data={"user_id": "unauthorized_user"},
        created_at=datetime(2024, 12, 18, 14, 0, 1)
    )


@pytest.fixture
def sample_authorized_access_event():
    """Sample authorized access control event for testing."""
    return EventReceived(
        id=2,
        device_id="AA:BB:CC:DD:EE:FF",
        timestamp=datetime(2024, 12, 18, 14, 0, 0),
        event_type="access_attempt",
        sensor_id=1,
        data={"user_id": "authorized_user"},
        created_at=datetime(2024, 12, 18, 14, 0, 1)
    )


@pytest.fixture
def sample_speed_event():
    """Sample speed violation event for testing."""
    return EventReceived(
        id=3,
        device_id="11:22:33:44:55:66",
        timestamp=datetime(2024, 12, 18, 14, 0, 0),
        event_type="speed_violation",
        sensor_id=2,
        data={"speed_kmh": 120, "location": "Zone A"},
        created_at=datetime(2024, 12, 18, 14, 0, 1)
    )


@pytest.fixture
def sample_safe_speed_event():
    """Sample safe speed event for testing."""
    return EventReceived(
        id=4,
        device_id="11:22:33:44:55:66",
        timestamp=datetime(2024, 12, 18, 14, 0, 0),
        event_type="speed_violation",
        sensor_id=2,
        data={"speed_kmh": 70, "location": "Zone A"},
        created_at=datetime(2024, 12, 18, 14, 0, 1)
    )


@pytest.fixture
def sample_intrusion_event():
    """Sample intrusion detection event for testing."""
    return EventReceived(
        id=5,
        device_id="77:88:99:AA:BB:CC",
        timestamp=datetime(2024, 12, 18, 22, 0, 0),  # After hours
        event_type="motion_detected",
        sensor_id=3,
        data={
            "zone": "Restricted Area",
            "confidence": 0.95,
            "photo_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        },
        created_at=datetime(2024, 12, 18, 22, 0, 1)
    )


@pytest.fixture
def sample_safe_motion_event():
    """Sample safe motion detection event for testing."""
    return EventReceived(
        id=6,
        device_id="77:88:99:AA:BB:CC",
        timestamp=datetime(2024, 12, 18, 12, 0, 0),  # During hours
        event_type="motion_detected",
        sensor_id=3,
        data={
            "zone": "Open Area",
            "confidence": 0.80,
            "photo_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        },
        created_at=datetime(2024, 12, 18, 12, 0, 1)
    ) 