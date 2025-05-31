import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.sensor import SensorCreate
from app.schemas.event import EventCreate


class TestSchemas:
    """Essential schema validation tests based on requirements."""

    def test_mac_address_valid_formats(self):
        """Test valid MAC address formats."""
        valid_macs = [
            "AA:BB:CC:DD:EE:FF",
            "00:11:22:33:44:55",
            "aa:bb:cc:dd:ee:ff"  # lowercase should be normalized
        ]
        
        for mac in valid_macs:
            sensor = SensorCreate(device_id=mac, device_type="access_controller")
            assert sensor.device_id == mac.upper()

    def test_mac_address_invalid_formats(self):
        """Test invalid MAC address formats."""
        invalid_macs = [
            "invalid-mac",
            "AA:BB:CC:DD:EE",      # too short
            "GG:HH:II:JJ:KK:LL",   # invalid hex
            "AA-BB-CC-DD-EE-FF",   # wrong separator
            ""
        ]
        
        for mac in invalid_macs:
            with pytest.raises(ValidationError):
                SensorCreate(device_id=mac, device_type="access_controller")

    def test_device_types_valid(self):
        """Test valid device types as per requirements."""
        valid_types = ["radar", "security_camera", "access_controller"]
        
        for device_type in valid_types:
            sensor = SensorCreate(device_id="AA:BB:CC:DD:EE:FF", device_type=device_type)
            assert sensor.device_type == device_type

    def test_device_type_invalid(self):
        """Test invalid device type."""
        with pytest.raises(ValidationError):
            SensorCreate(device_id="AA:BB:CC:DD:EE:FF", device_type="invalid_type")

    def test_event_create_basic(self):
        """Test basic event creation."""
        event = EventCreate(
            device_id="AA:BB:CC:DD:EE:FF",
            timestamp=datetime(2024, 12, 18, 14, 0, 0),
            event_type="access_attempt"
        )
        assert event.device_id == "AA:BB:CC:DD:EE:FF"
        assert event.event_type == "access_attempt"

    def test_event_create_with_access_fields(self):
        """Test event creation with access control fields."""
        event = EventCreate(
            device_id="AA:BB:CC:DD:EE:FF",
            timestamp=datetime(2024, 12, 18, 14, 0, 0),
            event_type="access_attempt",
            user_id="test_user"
        )
        assert event.user_id == "test_user"

    def test_event_create_with_speed_fields(self):
        """Test event creation with speed violation fields."""
        event = EventCreate(
            device_id="11:22:33:44:55:66",
            timestamp=datetime(2024, 12, 18, 14, 0, 0),
            event_type="speed_violation",
            speed_kmh=120,
            location="Zone A"
        )
        assert event.speed_kmh == 120
        assert event.location == "Zone A"

    def test_event_create_with_intrusion_fields(self):
        """Test event creation with intrusion detection fields."""
        event = EventCreate(
            device_id="77:88:99:AA:BB:CC",
            timestamp=datetime(2024, 12, 18, 22, 0, 0),
            event_type="motion_detected",
            zone="Restricted Area",
            confidence=0.95,
            photo_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        assert event.zone == "Restricted Area"
        assert event.confidence == 0.95 