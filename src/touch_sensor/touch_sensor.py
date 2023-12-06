from typing import NamedTuple
from enum import auto, Enum
import time

from config.pipe_config import TAP_DATA_PIPE
from config.touch_sensor_config import DEBOUNCE_TIME


class TapStatus(Enum):
    """Class for representing the status of a tap"""
    GOOD = auto()
    BAD = auto()


class Tap(NamedTuple):
    timestamp: float = 0.0
    status: TapStatus = TapStatus.BAD
    # order_id: str = ''
    # employee_name: str = ''


class TouchSensor:
    """Represents a touch sensor.

    Attributes:
        debounce_time: An int specifying the debounce time in seconds.
        tap_data_pipe: A string specifying the file path to the tap data pipe.
    """
        
    def __init__(
        self, 
        debounce_time: int = DEBOUNCE_TIME,
        tap_data_pipe: str = TAP_DATA_PIPE
    ) -> None:
        self.debounce_time = debounce_time
        self.tap_data_pipe = tap_data_pipe
        self.last_tap = Tap()
    
    def handle_tap(self) -> bool:
        timestamp = time.time()
        tap_status = TapStatus.BAD

        if (timestamp - self.last_tap.timestamp) >= self.debounce_time:
            tap_status = TapStatus.GOOD 
        tap = Tap(timestamp=timestamp, status=tap_status)
        
        self.pipe_tap_data(tap)
        
        if tap.status == TapStatus.GOOD:       
            # TODO Create record on Supabase
            # TODO: Fork child process to deal with record creation
            pass
        
        self.last_tap = tap  # Reset debounce timer
        return tap.status != TapStatus.BAD

    def pipe_tap_data(self, tap: NamedTuple) -> None:
        pass