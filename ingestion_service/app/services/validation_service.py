from typing import Dict, Any, Set
from app.domain.sensor_types import SensorDomain


class ValidationService:
    """Service for validating device and event combinations."""
    
    def __init__(self):
        self.domain = SensorDomain

    def validate_device_event_combination(self, device_type: str, event_type: str) -> bool:
        """Validate that device type can send this event type."""
        return self.domain.is_valid_device_event_combination(device_type, event_type)

    def get_allowed_event_type(self, device_type: str) -> str | None:
        """Get the event type allowed for a device type."""
        return self.domain.get_allowed_event_type(device_type)

    def validate_event_fields(self, event_type: str, provided_fields: Set[str]) -> tuple[bool, Set[str]]:
        """
        Validate that all required fields are present and no extra fields exist.
        """
        required_fields = self.domain.get_required_fields(event_type)
        if not required_fields:
            return False, provided_fields

        extra_fields = provided_fields - required_fields

        is_valid = len(extra_fields) == 0
        return is_valid, extra_fields

    def get_validation_error_message(self, device_type: str, event_type: str) -> str:
        """Get a descriptive error message for validation failures."""
        expected_event_type = self.get_allowed_event_type(device_type)
        if not expected_event_type:
            return f"Unknown device type '{device_type}'"

        return (
            f"Event type '{event_type}' not valid for device type '{device_type}'. "
            f"Expected '{expected_event_type}'"
        )


validation_service = ValidationService()
