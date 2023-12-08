import json
import os
import time

from utils.pipe_paths import TOUCH_SENSOR_TO_SCREEN_PIPE
from utils.utils import DEVICE_ID
from utils.touch_sensor_utils import *
from config.touch_sensor_config import *


class TouchSensor:
        
    def __init__(
        self, 
        debounce_time: int = DEBOUNCE_TIME,
        tap_data_pipe: str = TOUCH_SENSOR_TO_SCREEN_PIPE
    ) -> None:
        self.debounce_time = debounce_time
        self.tap_data_pipe = tap_data_pipe
        self.last_tap = Tap()
    
    def handle_tap(self) -> bool:
        timestamp = time.time()
        tap_status = TapStatus.BAD

        if (timestamp - self.last_tap.timestamp) >= self.debounce_time:
            tap_status = TapStatus.GOOD 
        
        tap = Tap(
            device_id=DEVICE_ID,
            timestamp=timestamp, 
            status=tap_status
        )
        
        self.pipe_tap_data(tap)
        
        if tap.status == TapStatus.GOOD:       
            # TODO Create record on Supabase
            # TODO: Fork child process to deal with record creation
            pass
        
        self.last_tap = tap  # Reset debounce timer
        return tap.status != TapStatus.BAD

    def pipe_tap_data(self, tap: NamedTuple) -> None:
        tap_data = dict(tap)

        if not os.path.exists(TOUCH_SENSOR_TO_SCREEN_PIPE):
            raise FileNotFoundError  # TODO: Determine error message format
        
        fd = os.open(TOUCH_SENSOR_TO_SCREEN_PIPE, os.O_WRONLY)
        with os.fdopen(fd, 'w') as pipeout:  # Convert file descriptor to fp
            json.dump(tap_data, pipeout)