import pytest
import requests
import base64
import os
from typing import Dict, List

# Test configuration
API_CONFIG = {
    "ingestion_base_url": "http://localhost:8000/api/v1",
    "alerting_base_url": "http://localhost:8001/api/v1", 
    "timeout": 30
}

@pytest.fixture(scope="session")
def session():
    """Create a requests session for the test suite"""
    with requests.Session() as s:
        yield s

@pytest.fixture(scope="session") 
def api_config():
    """API configuration for tests"""
    return API_CONFIG

@pytest.fixture(scope="session")
def test_images():
    """Test images for photo-related tests"""
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    
    with open(os.path.join(assets_dir, "intrusion-detection-1-alert.jpg"), "rb") as f:
        alert_image = base64.b64encode(f.read()).decode('utf-8')
    
    with open(os.path.join(assets_dir, "intrusion-detection-2-no-alert.jpg"), "rb") as f:
        no_alert_image = base64.b64encode(f.read()).decode('utf-8')
    
    return {
        "alert_image": alert_image,
        "no_alert_image": no_alert_image
    }

@pytest.fixture(scope="session")
def test_sensors():
    """Test sensor configurations"""
    return [
        {
            "device_id": "AA:BB:CC:DD:EE:FF",
            "device_type": "access_controller",
            "description": "Main entrance access controller"
        },
        {
            "device_id": "11:22:33:44:55:66", 
            "device_type": "radar",
            "description": "Speed monitoring radar"
        },
        {
            "device_id": "77:88:99:AA:BB:CC",
            "device_type": "security_camera", 
            "description": "Perimeter security camera"
        }
    ]

@pytest.fixture(scope="session")
def authorized_users():
    """List of authorized user IDs"""
    return ["authorized_user", "admin", "security_guard"]
