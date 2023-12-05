import time

class TouchSensor:
    def __init__(self, debounce: int, screen_pipe_path: str, cloud_db_pipe_path: str) -> None:
        self.debounce = debounce
        self.screen_pipe_path = screen_pipe_path
        self.cloud_db_pipe_path = cloud_db_pipe_path
    
    def tap(self) -> bool:
        pass

    def pipe_data_to_screen(self, type: str, timestamp: time.time_struct) -> None:
        pass