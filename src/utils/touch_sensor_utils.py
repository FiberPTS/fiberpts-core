from time import struct_time
from typing import Tuple, Iterator, NamedTuple

from src.utils.utils import TapStatus


class Tap(NamedTuple):
    """Stores information describing a tap event.

    Attributes:
        device_id: The ID of the device from which the tap was made.
        timestamp: The timestamp at which the tap was made.
        status: A TapStatus indicating the status of the tap.
    """
    device_id: str = ''
    timestamp: struct_time | float = 0.0
    status: TapStatus = TapStatus.BAD

    def __iter__(self) -> Iterator[Tuple[str, str | struct_time | float]]:
        """Enable iteration over Tap attributes. 
        This method allows the Tap instance to be converted to a dictionary.
        
        Args:
            None

        Returns:
            An iterator over the Tap attributes.
        """
        for name, _ in self.__annotations__.items():
            value = getattr(self, name)
            if isinstance(value, TapStatus):
                yield (name, value.name)
            else:
                yield (name, value)
