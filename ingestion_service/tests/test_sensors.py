import pytest
from httpx import AsyncClient


class TestSensorsAPI:
    """Essential test cases for sensor API endpoints based on requirements."""

    async def test_create_sensor_success(self, client: AsyncClient, sample_sensor_data):
        """Test successful sensor creation with MAC validation."""
        response = await client.post("/api/v1/sensors/", json=sample_sensor_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == sample_sensor_data["device_id"]
        assert data["device_type"] == sample_sensor_data["device_type"]
        assert "id" in data

    async def test_create_sensor_invalid_mac_address(self, client: AsyncClient):
        """Test sensor creation with invalid MAC address format."""
        invalid_data = {
            "device_id": "invalid-mac",
            "device_type": "radar"
        }
        response = await client.post("/api/v1/sensors/", json=invalid_data)
        assert response.status_code == 422

    async def test_create_sensor_invalid_device_type(self, client: AsyncClient):
        """Test sensor creation with invalid device type."""
        invalid_data = {
            "device_id": "AA:BB:CC:DD:EE:FF",
            "device_type": "invalid_type"
        }
        response = await client.post("/api/v1/sensors/", json=invalid_data)
        assert response.status_code == 422

    async def test_create_duplicate_sensor(self, client: AsyncClient, sample_sensor_data):
        """Test creating a sensor with duplicate device_id."""
        await client.post("/api/v1/sensors/", json=sample_sensor_data)
        response = await client.post("/api/v1/sensors/", json=sample_sensor_data)
        assert response.status_code == 400

    async def test_get_sensor_by_device_id(self, client: AsyncClient, sample_sensor_data):
        """Test retrieving sensor by device ID for validation."""
        await client.post("/api/v1/sensors/", json=sample_sensor_data)
        
        device_id = sample_sensor_data["device_id"]
        response = await client.get(f"/api/v1/sensors/{device_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == device_id

    async def test_get_sensor_not_found(self, client: AsyncClient):
        """Test getting unregistered sensor."""
        response = await client.get("/api/v1/sensors/FF:FF:FF:FF:FF:FF")
        assert response.status_code == 404 