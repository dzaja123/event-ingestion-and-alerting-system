import re
from typing import Annotated
from pydantic import AfterValidator


# Regex for MAC address validation (common formats)
MAC_ADDRESS_REGEX = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|"
    r"^([0-9A-Fa-f]{4}[.]){2}([0-9A-Fa-f]{4})$|"
    r"^([0-9A-Fa-f]{2}){6}$"
)


def validate_mac_address(value: str) -> str:
    if not MAC_ADDRESS_REGEX.match(value):
        raise ValueError("Invalid MAC address format")
    return value.upper().replace("-", ":").replace(".", ":") # Normalize


MACAddress = Annotated[str, AfterValidator(validate_mac_address)]
