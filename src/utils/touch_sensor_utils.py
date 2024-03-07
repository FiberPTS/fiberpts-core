import time
from typing import NamedTuple

from src.utils.utils import TapStatus

class Tap(NamedTuple):
    """Stores information describing a tap event.

    Attributes:
        device_id: The ID of the device from which the tap was made.
        timestamp: The timestamp at which the tap was made.
        status: A TapStatus indicating the status of the tap.
    """
    device_id: str = ''
    timestamp: time.struct_time = 0.0
    status: TapStatus = TapStatus.BAD

    def __iter__(self):
        """Enable iteration over Tap attributes.

        This method allows the Tap instance to be converted to a dictionary.
        """
        for name, _ in self.__annotations__.items():
            value = getattr(self, name)
            if isinstance(value, TapStatus):
                yield name, value.name  # or value.value if you prefer the numeric value
            else:
                yield name, value
