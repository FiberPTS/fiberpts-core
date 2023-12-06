from enum import auto, Enum
import time

from config.pipe_config import TAP_DATA_PIPE
from config.touch_sensor_config import DEBOUNCE_TIME


class TapStatus(Enum):
    """Class for representing the status of a tap"""
    GOOD = auto()
    BAD = auto()


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
    
    def tap(self) -> bool:
        timestamp = time.time()

        tap_status = self.check_debounce(timestamp)
        self.pipe_tap_data(tap_status, timestamp)

        if tap_status == TapStatus.GOOD:       
            # TODO Create record on Supabase
            # TODO: Fork child process to deal with record creation
            pass

        return tap_status != TapStatus.BAD
    
    def check_debounce(self, timestamp: float) -> TapStatus:
        pass

    def pipe_tap_data(self, tap_status: str, timestamp: float) -> None:
        pass