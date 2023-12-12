from datetime import timedelta
import json
import os
import select

import gpiod
from gpiod.line import Bias, Edge

from src.cloud_db.cloud_db import CloudDBClient
from config.touch_sensor_config import *
from src.utils.paths import TOUCH_SENSOR_TO_SCREEN_PIPE
from src.utils.touch_sensor_utils import *
from src.utils.utils import get_machine_id, TapStatus


class TouchSensor:
    """Represents a touch sensor.

    Attributes:
        debounce_time: Minimum time interval (in seconds) to consider consecutive taps as distinct.
        screen_pipe: File path to the FIFO used for IPC with the screen module.
        cloud_db: An instance of CloudDBClient for database interactions.
        last_tap: The last recorded tap.
    """

    def __init__(
        self,
        debounce_time: int = DEBOUNCE_TIME,
        line_offset: int = TOUCH_SENSOR_LINE_OFFSET,
        chip: int = TOUCH_SENSOR_CHIP,
        screen_pipe: str = TOUCH_SENSOR_TO_SCREEN_PIPE                   
    ) -> None:
        """
        Initializes the TouchSensor with specified debounce time and pipe path.

        Args:
            debounce_time: An integer specifying the debounce time in seconds.
            screen_pipe: File path to the screen FIFO.
        """
        self.debounce_time = debounce_time
        self.line_offset = line_offset
        self.chip_path = f"/dev/gpiochip{chip}"
        self.screen_pipe = screen_pipe
        self.cloud_db = CloudDBClient()
        self.last_tap = Tap()

    def handle_tap(self) -> bool:
        """Handles a tap event.

        The method records the tap event, validates it based on the debounce time,
        sends valid tap data to both the scren FIFO and the cloud database,
        and updates the last tap event.

        Returns:
            A boolean indicating whether the tap was valid (True) or not (False).
        """
        timestamp = time.time()
        tap_status = TapStatus.BAD

        if (timestamp - self.last_tap.timestamp) >= self.debounce_time:
            tap_status = TapStatus.GOOD

        tap = Tap(
            machine_id=get_machine_id(), 
            timestamp=timestamp,
            status=tap_status
        )

        self.pipe_tap_data(tap)

        if tap.status == TapStatus.GOOD:
            # TODO: Implement child process creation for record handling.
            self.cloud_db.insert_tap_data(tap)
        
        self.last_tap = tap
        return tap.status != TapStatus.BAD

    def pipe_tap_data(self, tap: Tap) -> None:
        """Sends tap data to named pipe for IPC with screen module.

        Args:
            tap: A Tap instance containing the tap data.
        
        Raises:
            FileNotFoundError: If the pipeline path does not exist.
        """
        tap_data = dict(tap)

        try:
            fd = os.open(self.screen_pipe, os.O_WRONLY)
        except FileNotFoundError:
            raise FileNotFoundError  # TODO: Determine error message format
        else:
            with os.fdopen(fd, 'w') as pipeout:  # Convert file descriptor to file pointer
                json.dump(tap_data, pipeout)


    def run(self) -> None:
        """Monitors the GPIO line for tap events and processes them.

        Continuously checks a specific GPIO line for voltage changes. If a change is detected,
        interprets it as a tap event and triggers the tap handling process.
        """
        # Configure the GPIO line
        with gpiod.request_lines(
            self.chip_path,
            consumer="async-watch-touch",
            config={
                self.line_offset: gpiod.LineSettings(
                    edge_detection=Edge.BOTH,  # Detect both rising and falling edges
                    bias=Bias.PULL_DOWN,  # No internal pull-up/pull-down resistor needed
                    debounce_period=timedelta(milliseconds=50)  # Adjust based on your requirement
                )
            },
        ) as request:
            poll = select.poll()
            poll.register(request.fd, select.POLLIN)
            while True:
                # Wait for an event on the GPIO line with a timeout
                if poll.poll(1000):  # Timeout of 1000 milliseconds (1 second)
                    for event in request.read_edge_events():
                        print(event)
                        if event.type == event.Type.RISING_EDGE:
                            self.handle_tap()  # Handle the tap event
                else:
                    # No event within the timeout period
                    print("Waiting for tap event...")


if __name__ == "__main__":
    touch_sensor = TouchSensor()
    touch_sensor.run()