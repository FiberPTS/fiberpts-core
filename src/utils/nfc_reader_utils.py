from typing import NamedTuple

from src.utils.utils import NFCType

class NFCTag(NamedTuple):
    """Stores information describing a tap event.

    Attributes:
        device_id: The ID of the device from which the tap was made.
        timestamp: The timestamp at which the tap was made.
        status: A TapStatus indicating the status of the tap.
    """
    device_id: str = ''
    type: NFCType = NFCType.ORDER
    value: str = ''
    tag_id: str = ''


    def __iter__(self):
        """Enable iteration over NFCTag attributes.

        This method allows the NFCTag instance to be converted to a dictionary.
        """
        for name, _ in self.__annotations__.items():
            value = getattr(self, name)
            if isinstance(value, NFCTag):
                yield name, value.name  # or value.value if you prefer the numeric value
            else:
                yield name, value
