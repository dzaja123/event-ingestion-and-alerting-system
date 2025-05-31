import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.alert import AlertBase, AlertCreate


class TestAlertSchemas:
    """Essential test cases for alert schema validation based on requirements."""

    def test_alert_base_valid(self):
        """Test valid alert base schema."""
        alert_data = {
            "device_id": "AA:BB:CC:DD:EE:FF",
            "alert_type": "unauthorized_access",
            "timestamp": datetime(2024, 12, 18, 14, 0, 0)
        }
        
        alert = AlertBase(**alert_data)
        
        assert alert.device_id == "AA:BB:CC:DD:EE:FF"
        assert alert.alert_type == "unauthorized_access"

    def test_alert_create_inherits_from_base(self):
        """Test that AlertCreate inherits from AlertBase."""
        alert_data = {
            "event_id": 2,
            "device_id": "BB:CC:DD:EE:FF:AA",
            "alert_type": "speed_violation",
            "timestamp": datetime(2024, 12, 18, 15, 0, 0)
        }
        
        alert = AlertCreate(**alert_data)
        
        assert isinstance(alert, AlertBase)
        assert alert.alert_type == "speed_violation"
        assert alert.event_id == 2

    def test_alert_types_valid(self):
        """Test valid alert types."""
        valid_types = ["unauthorized_access", "speed_violation", "intrusion_detection"]
        
        for alert_type in valid_types:
            alert_data = {
                "device_id": "AA:BB:CC:DD:EE:FF",
                "alert_type": alert_type,
                "timestamp": datetime(2024, 12, 18, 14, 0, 0)
            }
            
            alert = AlertCreate(**alert_data)
            assert alert.alert_type == alert_type

    def test_alert_type_invalid(self):
        """Test invalid alert type."""
        alert_data = {
            "device_id": "AA:BB:CC:DD:EE:FF",
            "alert_type": "invalid_type",
            "timestamp": datetime(2024, 12, 18, 14, 0, 0)
        }
        
        with pytest.raises(ValidationError) as exc:
            AlertCreate(**alert_data)
        
        assert "alert_type" in str(exc.value)

    def test_required_fields(self):
        """Test that all required fields are validated."""
        # Missing device_id
        with pytest.raises(ValidationError):
            AlertCreate(
                alert_type="unauthorized_access",
                timestamp=datetime(2024, 12, 18, 14, 0, 0)
            )
        
        # Missing alert_type
        with pytest.raises(ValidationError):
            AlertCreate(
                device_id="AA:BB:CC:DD:EE:FF",
                timestamp=datetime(2024, 12, 18, 14, 0, 0)
            )

    def test_mac_address_validation(self):
        """Test MAC address validation in alert schemas."""
        # Valid MAC address
        alert = AlertCreate(
            device_id="AA:BB:CC:DD:EE:FF",
            alert_type="unauthorized_access",
            timestamp=datetime(2024, 12, 18, 14, 0, 0)
        )
        assert alert.device_id == "AA:BB:CC:DD:EE:FF"
        
        # Invalid MAC address should raise ValidationError
        with pytest.raises(ValidationError):
            AlertCreate(
                device_id="invalid-mac",
                alert_type="unauthorized_access",
                timestamp=datetime(2024, 12, 18, 14, 0, 0)
            ) 