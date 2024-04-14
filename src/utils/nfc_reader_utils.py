import time
from typing import Dict, Any, NamedTuple

from src.utils.utils import NFCType

class NFCTag(NamedTuple):
    """Stores information describing an NFC Tag.

    Attributes:
        device_id: The ID of the device from which the tap was made.
        type: An NFCType represnting what this NFC tag correponds to; employee, order, or None
        data: A dictionary containing relevant data about either an order or employee.
        tag_id: A str containing the unique id of an NFC tag. 
    """
    device_id: str = ''
    timestamp: time.struct_time = 0.0
    type: NFCType = NFCType.NONE
    data: Dict[str, Any] = {}
    tag_id: str = ''


    def __iter__(self):
        """Enable iteration over NFCTag attributes.

        This method allows the NFCTag instance to be converted to a dictionary.
        """
        for name, _ in self.__annotations__.items():
            value = getattr(self, name)
            if isinstance(value, NFCType):
                yield name, value.name  # or value.value if you prefer the numeric value
            else:
                yield name, value
