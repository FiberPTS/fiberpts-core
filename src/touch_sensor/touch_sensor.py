import time

class TouchSensor:
    def __init__(self, debounce: int, screen_pipe: str, cloud_db_pipe: str) -> None:
        self.debounce = debounce
        self.screen_pipe = screen_pipe
        self.cloud_db_pipe = cloud_db_pipe
    
    def tap(self) -> bool:
        pass

    def pipe_data_to_screen(self, type: str, timestamp: time.time_struct) -> None:
        pass