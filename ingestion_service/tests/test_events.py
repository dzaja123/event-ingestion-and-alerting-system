import pytest
from httpx import AsyncClient


class TestEventsAPI:
    """Essential test cases for events API based on requirements."""

    async def test_create_event_success(self, client: AsyncClient, sample_sensor_data, sample_event_data):
        """Test successful event creation with registered sensor."""
        await client.post("/api/v1/sensors/", json=sample_sensor_data)
        response = await client.post("/api/v1/events/", json=sample_event_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == sample_event_data["device_id"]
        assert data["event_type"] == sample_event_data["event_type"]
        assert "id" in data

    async def test_create_event_unregistered_sensor(self, client: AsyncClient, sample_event_data):
        """Test event creation with unregistered sensor should fail."""
        response = await client.post("/api/v1/events/", json=sample_event_data)
        assert response.status_code == 403
        assert "not registered" in response.json()["detail"]

    async def test_create_event_invalid_mac_address(self, client: AsyncClient):
        """Test event creation with invalid MAC address."""
        invalid_event = {
            "device_id": "invalid-mac",
            "timestamp": "2024-12-18T14:00:00Z",
            "event_type": "access_attempt"
        }
        response = await client.post("/api/v1/events/", json=invalid_event)
        assert response.status_code == 422

    async def test_create_access_event(self, client: AsyncClient):
        """Test creating access control event (for unauthorized access detection)."""
        sensor_data = {
            "device_id": "AA:BB:CC:DD:EE:FF",
            "device_type": "access_controller"
        }
        await client.post("/api/v1/sensors/", json=sensor_data)
        
        event_data = {
            "device_id": "AA:BB:CC:DD:EE:FF",
            "timestamp": "2024-12-18T14:00:00Z",
            "event_type": "access_attempt",
            "user_id": "test_user"
        }
        response = await client.post("/api/v1/events/", json=event_data)
        assert response.status_code == 201

    async def test_create_speed_event(self, client: AsyncClient):
        """Test creating speed violation event."""
        sensor_data = {
            "device_id": "11:22:33:44:55:66",
            "device_type": "radar"
        }
        await client.post("/api/v1/sensors/", json=sensor_data)
        
        event_data = {
            "device_id": "11:22:33:44:55:66",
            "timestamp": "2024-12-18T14:00:00Z",
            "event_type": "speed_violation",
            "speed_kmh": 120,
            "location": "Zone A"
        }
        response = await client.post("/api/v1/events/", json=event_data)
        assert response.status_code == 201

    async def test_create_intrusion_event(self, client: AsyncClient):
        """Test creating intrusion detection event."""
        sensor_data = {
            "device_id": "77:88:99:AA:BB:CC",
            "device_type": "security_camera"
        }
        await client.post("/api/v1/sensors/", json=sensor_data)
        
        event_data = {
            "device_id": "77:88:99:AA:BB:CC",
            "timestamp": "2024-12-18T22:00:00Z",
            "event_type": "motion_detected",
            "zone": "Restricted Area",
            "confidence": 0.95,
            "photo_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        }
        response = await client.post("/api/v1/events/", json=event_data)
        assert response.status_code == 201

    async def test_get_events_basic(self, client: AsyncClient, sample_sensor_data, sample_event_data):
        """Test basic GET /events endpoint."""
        await client.post("/api/v1/sensors/", json=sample_sensor_data)
        await client.post("/api/v1/events/", json=sample_event_data)
        
        response = await client.get("/api/v1/events/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_message_queue_integration(self, client: AsyncClient, sample_sensor_data, sample_event_data, mock_message_queue):
        """Test that events are published to message queue for alerting service."""
        await client.post("/api/v1/sensors/", json=sample_sensor_data)
        await client.post("/api/v1/events/", json=sample_event_data)
        
        mock_message_queue.publish_event.assert_called_once() 