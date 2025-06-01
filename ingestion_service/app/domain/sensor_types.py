from enum import Enum
from typing import Dict, Set
from dataclasses import dataclass


class DeviceType(str, Enum):
    """Supported IoT device types."""
    ACCESS_CONTROLLER = "access_controller"
    RADAR = "radar"
    SECURITY_CAMERA = "security_camera"


class EventType(str, Enum):
    """Supported event types."""
    ACCESS_ATTEMPT = "access_attempt"
    SPEED_VIOLATION = "speed_violation"
    MOTION_DETECTED = "motion_detected"


@dataclass(frozen=True)
class SensorRule:
    """Domain rule for sensor type validation."""
    device_type: DeviceType
    allowed_event_type: EventType
    required_fields: Set[str]
    description: str


class SensorDomain:
    """Domain logic for sensor validation"""

    SENSOR_RULES = [
        SensorRule(
            device_type=DeviceType.ACCESS_CONTROLLER,
            allowed_event_type=EventType.ACCESS_ATTEMPT,
            required_fields={'device_id', 'timestamp', 'event_type', 'user_id'},
            description="Access control systems for doors/gates"
        ),
        SensorRule(
            device_type=DeviceType.RADAR,
            allowed_event_type=EventType.SPEED_VIOLATION,
            required_fields={'device_id', 'timestamp', 'event_type', 'speed_kmh', 'location'},
            description="Speed monitoring radar systems"
        ),
        SensorRule(
            device_type=DeviceType.SECURITY_CAMERA,
            allowed_event_type=EventType.MOTION_DETECTED,
            required_fields={'device_id', 'timestamp', 'event_type', 'zone', 'confidence', 'photo_base64'},
            description="Motion detection security cameras"
        )
    ]

    @classmethod
    def get_allowed_event_type(cls, device_type: str) -> str | None:
        """Get allowed event type for a device type"""
        for rule in cls.SENSOR_RULES:
            if rule.device_type.value == device_type:
                return rule.allowed_event_type.value
        return None

    @classmethod
    def get_required_fields(cls, event_type: str) -> Set[str] | None:
        """Get required fields for an event type"""
        for rule in cls.SENSOR_RULES:
            if rule.allowed_event_type.value == event_type:
                return rule.required_fields
        return None

    @classmethod
    def is_valid_device_event_combination(cls, device_type: str, event_type: str) -> bool:
        """Validate device type and event type combination"""
        allowed_event = cls.get_allowed_event_type(device_type)
        return allowed_event == event_type

    @classmethod
    def get_device_to_event_mapping(cls) -> Dict[str, str]:
        """Get complete mapping of device types to event types"""
        return {
            rule.device_type.value: rule.allowed_event_type.value
            for rule in cls.SENSOR_RULES
        }

    @classmethod
    def is_valid_device_type(cls, device_type: str) -> bool:
        """Check if device type is supported"""
        return any(rule.device_type.value == device_type for rule in cls.SENSOR_RULES)

    @classmethod
    def is_valid_event_type(cls, event_type: str) -> bool:
        """Check if event type is supported"""
        return any(rule.allowed_event_type.value == event_type for rule in cls.SENSOR_RULES)
