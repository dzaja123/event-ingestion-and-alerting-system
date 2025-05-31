import re
from typing import Annotated
from pydantic import Field


# Regex for MAC address validation
MAC_ADDRESS_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$")


def validate_mac_address(value: str) -> str:
    """Validate and normalize MAC address to uppercase colon-separated format."""
    if not isinstance(value, str) or not value:
        raise ValueError("MAC address must be a non-empty string")

    # Check if it matches the expected format
    if not MAC_ADDRESS_REGEX.match(value):
        raise ValueError("Invalid MAC address format. Expected format: XX:XX:XX:XX:XX:XX")

    # Normalize to uppercase
    return value.upper()


# Define MAC address type
MACAddress = Annotated[
    str, 
    Field(
        pattern=r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$",
        description="MAC address in format XX:XX:XX:XX:XX:XX"
    )
]
