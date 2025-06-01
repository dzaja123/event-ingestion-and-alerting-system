import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.sensor import SensorCreate
from app.schemas.event import EventCreate


class TestSchemas:
    """Schema validation tests."""

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

    def test_access_control_event_valid(self):
        """Test valid access control event creation."""
        event = EventCreate.model_validate({
            "device_id": "AA:BB:CC:DD:EE:FF",
            "timestamp": "2024-12-18T14:00:00Z",
            "event_type": "access_attempt",
            "user_id": "test_user"
        })
        assert event.root.device_id == "AA:BB:CC:DD:EE:FF"
        assert event.root.event_type == "access_attempt"
        assert event.root.user_id == "test_user"

    def test_speed_violation_event_valid(self):
        """Test valid speed violation event creation."""
        event = EventCreate.model_validate({
            "device_id": "11:22:33:44:55:66",
            "timestamp": "2024-12-18T14:00:00Z",
            "event_type": "speed_violation",
            "speed_kmh": 120,
            "location": "Zone A"
        })
        assert event.root.device_id == "11:22:33:44:55:66"
        assert event.root.event_type == "speed_violation"
        assert event.root.speed_kmh == 120
        assert event.root.location == "Zone A"

    def test_intrusion_detection_event_valid(self):
        """Test valid intrusion detection event creation."""
        event = EventCreate.model_validate({
            "device_id": "77:88:99:AA:BB:CC",
            "timestamp": "2024-12-18T22:00:00Z",
            "event_type": "motion_detected",
            "zone": "Restricted Area",
            "confidence": 0.95,
            "photo_base64": "dGVzdA=="
        })
        assert event.root.device_id == "77:88:99:AA:BB:CC"
        assert event.root.event_type == "motion_detected"
        assert event.root.zone == "Restricted Area"
        assert event.root.confidence == 0.95
        assert event.root.photo_base64 == "dGVzdA=="

    def test_access_control_event_missing_user_id(self):
        """Test access control event missing required user_id field."""
        with pytest.raises(ValidationError):
            EventCreate.model_validate({
                "device_id": "AA:BB:CC:DD:EE:FF",
                "timestamp": "2024-12-18T14:00:00Z",
                "event_type": "access_attempt"
                # Missing user_id
            })

    def test_speed_violation_event_missing_fields(self):
        """Test speed violation event missing required fields."""
        with pytest.raises(ValidationError):
            EventCreate.model_validate({
                "device_id": "11:22:33:44:55:66",
                "timestamp": "2024-12-18T14:00:00Z",
                "event_type": "speed_violation",
                "speed_kmh": 120
                # Missing location
            })

    def test_intrusion_detection_event_missing_fields(self):
        """Test intrusion detection event missing required fields."""
        with pytest.raises(ValidationError):
            EventCreate.model_validate({
                "device_id": "77:88:99:AA:BB:CC",
                "timestamp": "2024-12-18T22:00:00Z",
                "event_type": "motion_detected",
                "zone": "Restricted Area"
                # Missing confidence and photo_base64
            })

    def test_mixed_fields_rejected(self):
        """Test that mixed fields from different event types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EventCreate.model_validate({
                "device_id": "AA:BB:CC:DD:EE:FF",
                "timestamp": "2024-12-18T14:00:00Z",
                "event_type": "access_attempt",
                "user_id": "test_user",
                "speed_kmh": 120  # This should not be allowed for access_attempt
            })
        assert "Extra fields not allowed" in str(exc_info.value)

    def test_invalid_base64_photo(self):
        """Test invalid base64 photo validation."""
        with pytest.raises(ValidationError):
            EventCreate.model_validate({
                "device_id": "77:88:99:AA:BB:CC",
                "timestamp": "2024-12-18T22:00:00Z",
                "event_type": "motion_detected",
                "zone": "Restricted Area",
                "confidence": 0.95,
                "photo_base64": "invalid_base64!"
            })

    def test_speed_validation_bounds(self):
        """Test speed validation bounds (0-300 km/h)."""
        # Valid speed
        event = EventCreate.model_validate({
            "device_id": "11:22:33:44:55:66",
            "timestamp": "2024-12-18T14:00:00Z",
            "event_type": "speed_violation",
            "speed_kmh": 150,
            "location": "Zone A"
        })
        assert event.root.speed_kmh == 150

        # Invalid speed (too high)
        with pytest.raises(ValidationError):
            EventCreate.model_validate({
                "device_id": "11:22:33:44:55:66",
                "timestamp": "2024-12-18T14:00:00Z",
                "event_type": "speed_violation",
                "speed_kmh": 350,  # Above 300 limit
                "location": "Zone A"
            })

    def test_confidence_validation_bounds(self):
        """Test confidence validation bounds (0.0-1.0)."""
        # Valid confidence
        event = EventCreate.model_validate({
            "device_id": "77:88:99:AA:BB:CC",
            "timestamp": "2024-12-18T22:00:00Z",
            "event_type": "motion_detected",
            "zone": "Restricted Area",
            "confidence": 0.75,
            "photo_base64": "dGVzdA=="
        })
        assert event.root.confidence == 0.75

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            EventCreate.model_validate({
                "device_id": "77:88:99:AA:BB:CC",
                "timestamp": "2024-12-18T22:00:00Z",
                "event_type": "motion_detected",
                "zone": "Restricted Area",
                "confidence": 1.5,  # Above 1.0 limit
                "photo_base64": "dGVzdA=="
            })
