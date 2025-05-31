import pytest
from httpx import AsyncClient
from datetime import datetime

from app.schemas.alert import AlertCreate


class TestAlertsAPI:
    """Essential test cases for alerts API endpoints based on requirements."""

    async def test_get_alerts_empty(self, client: AsyncClient):
        """Test getting alerts when none exist."""
        response = await client.get("/api/v1/alerts/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_and_get_alert(self, client: AsyncClient, db_session):
        """Test creating an alert and retrieving it."""
        from app.crud.alert import alert
        
        alert_data = AlertCreate(
            event_id=1,
            device_id="AA:BB:CC:DD:EE:FF",
            alert_type="unauthorized_access",
            timestamp=datetime(2024, 12, 18, 14, 0, 0)
        )
        
        await alert.create(db=db_session, obj_in=alert_data)
        
        response = await client.get("/api/v1/alerts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["alert_type"] == "unauthorized_access"

    async def test_get_alerts_filter_by_alert_type(self, client: AsyncClient, db_session):
        """Test filtering alerts by alert type."""
        from app.crud.alert import alert
        
        # Create alerts of different types
        alerts = [
            AlertCreate(
                event_id=1,
                device_id="AA:BB:CC:DD:EE:FF",
                alert_type="unauthorized_access",
                timestamp=datetime(2024, 12, 18, 14, 0, 0)
            ),
            AlertCreate(
                event_id=2,
                device_id="BB:CC:DD:EE:FF:AA",
                alert_type="speed_violation",
                timestamp=datetime(2024, 12, 18, 15, 0, 0)
            )
        ]
        
        for alert_data in alerts:
            await alert.create(db=db_session, obj_in=alert_data)
        
        response = await client.get("/api/v1/alerts/?alert_type=unauthorized_access")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["alert_type"] == "unauthorized_access"

    async def test_get_alerts_filter_by_device_id(self, client: AsyncClient, db_session):
        """Test filtering alerts by device ID."""
        from app.crud.alert import alert
        
        device_id = "AA:BB:CC:DD:EE:FF"
        alert_data = AlertCreate(
            event_id=1,
            device_id=device_id,
            alert_type="speed_violation",
            timestamp=datetime(2024, 12, 18, 14, 0, 0)
        )
        
        await alert.create(db=db_session, obj_in=alert_data)
        
        response = await client.get(f"/api/v1/alerts/?device_id={device_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["device_id"] == device_id

    async def test_get_alert_by_id_success(self, client: AsyncClient, db_session):
        """Test getting specific alert by ID."""
        from app.crud.alert import alert
        
        alert_data = AlertCreate(
            event_id=1,
            device_id="AA:BB:CC:DD:EE:FF",
            alert_type="intrusion_detection",
            timestamp=datetime(2024, 12, 18, 14, 0, 0)
        )
        
        created_alert = await alert.create(db=db_session, obj_in=alert_data)
        
        response = await client.get(f"/api/v1/alerts/{created_alert.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_alert.id
        assert data["alert_type"] == "intrusion_detection"

    async def test_get_alert_by_id_not_found(self, client: AsyncClient):
        """Test getting non-existent alert."""
        response = await client.get("/api/v1/alerts/999")
        assert response.status_code == 404

    async def test_health_endpoint(self, client: AsyncClient, mock_cache_service):
        """Test health check endpoint."""
        from unittest.mock import AsyncMock, MagicMock
        from app.services.rabbitmq_consumer import rabbitmq_consumer
        
        # Mock Redis ping
        mock_cache_service.redis_client.ping = AsyncMock(return_value=True)
        
        # Mock RabbitMQ connection
        mock_connection = MagicMock()
        mock_connection.is_closed = False
        rabbitmq_consumer.connection = mock_connection
        rabbitmq_consumer.consuming = True
        
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "alerting_service"
        assert "dependencies" in data
        assert "consuming" in data
        assert data["dependencies"]["database"] == "healthy"
        assert data["dependencies"]["redis"] == "healthy"
        assert data["dependencies"]["rabbitmq"] == "healthy" 