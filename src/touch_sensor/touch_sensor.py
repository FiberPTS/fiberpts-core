import time


class TouchSensor:
    def __init__(self, debounce_time: int, tap_data_pipe: str) -> None:
        self.debounce_time = debounce_time
        self.tap_data_pipe = tap_data_pipe
    
    def tap(self) -> bool:
        pass
    
    def pipe_tap_data(self, type: str, timestamp: time.struct_time) -> None:
        pass