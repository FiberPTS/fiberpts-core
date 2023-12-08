from enum import auto, Enum
from typing import NamedTuple

from utils import ftimestamp


from enum import Enum, auto
from typing import NamedTuple

class TapStatus(Enum):
    """Represents the status of a tap."""
    GOOD = auto()
    BAD = auto()

    def __repr__(self):
        return f'{self.name}'


class Tap(NamedTuple):
    """Stores information describing a tap event.

    Attributes:
        device_id: The ID of the device from which the tap was made.
        timestamp: The timestamp at which the tap was made.
        status: A TapStatus indicating the status of the tap.
    """
    device_id: str = ''
    timestamp: float = 0.0
    status: TapStatus = TapStatus.BAD

    def __iter__(self):
        """Enable iteration over Tap attributes.

        This method allows the Tap instance to be converted to a dictionary.
        """
        for name, _ in self.__annotations__.items():
            yield name, getattr(self, name)


def tap_to_db_entry(tap: Tap) -> dict:
    """Convert a Tap instance to a database entry format.

    Args:
        tap: A Tap instance to be converted.

    Returns:
        A dictionary representing the tap suitable for database entry.
    """
    tap_entry = {
        'timestamp': ftimestamp(tap.timestamp),
        'device_id': tap.device_id
    }
    return tap_entry
