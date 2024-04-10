import json
import os
import logging
import logging.config

import gpiod

from src.cloud_db.cloud_db import CloudDBClient
from config.touch_sensor_config import *
from src.utils.paths import (TOUCH_SENSOR_TO_SCREEN_PIPE, PROJECT_DIR)
from src.utils.touch_sensor_utils import *
from src.utils.utils import get_device_id, TapStatus

logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])


class TouchSensor:
    """Represents a touch sensor.

    Attributes:
        cloud_db: An instance of CloudDBClient for database interactions.
        last_tap: The last recorded tap.
    """

    def __init__(self) -> None:
        """Initializes the TouchSensor with specified debounce time and pipe path.
        
        Args:
            None

        Returns:
            None
        """
        self.device_id = get_device_id()
        self.cloud_db = CloudDBClient()
        self.last_tap = Tap()

    def handle_tap(self) -> bool:
        """Handles a tap event.

        The method records the tap event, validates it based on the debounce time,
        sends valid tap data to both the scren FIFO and the cloud database,
        and updates the last tap event.
        
        Args:
            None

        Returns:
            A boolean indicating whether the tap was valid (True) or not (False).
        """
        timestamp = time.time()
        tap_status = TapStatus.BAD

        if (timestamp - self.last_tap.timestamp) >= DEBOUNCE_TIME:
            tap_status = TapStatus.GOOD

        tap = Tap(device_id=self.device_id, timestamp=timestamp, status=tap_status)
        logger.info(f"Device Id: {tap.device_id}, \
              Timestamp: {tap.timestamp}, \
              Is Valid: {tap.status == TapStatus.GOOD}")

        self.pipe_tap_data(tap)

        is_valid_tap = tap.status == TapStatus.GOOD
        if is_valid_tap:
            # TODO: Implement child process creation for record handling.
            self.cloud_db.insert_tap_data(tap)

        self.last_tap = tap
        return is_valid_tap

    def pipe_tap_data(self, tap: Tap) -> None:
        """Sends tap data to named pipe for IPC with screen module.

        Args:
            tap: A Tap instance containing the tap data.
        
        Returns:
            None

        Raises:
            FileNotFoundError: If the pipeline path does not exist.
        """
        logger.info('Sending tap data to screen')
        tap_data = dict(tap)

        try:
            with open(TOUCH_SENSOR_TO_SCREEN_PIPE, 'a') as pipeout:
                json.dump(tap_data, pipeout)
                pipeout.write('\n')
                pipeout.flush()
        except FileNotFoundError:
            logger.error('Named pipe not found')
            raise FileNotFoundError('Named pipe not found')
        except BrokenPipeError:
            logger.error('Cannot write to pipe - broken pipe')
        except Exception as e:
            logger.error(f"Error writing to pipe: {e}")

    def run(self) -> None:
        """Monitors the GPIO line for tap events and processes them.

        Continuously checks a specific GPIO line for voltage changes. If a change is detected,
        interprets it as a tap event and triggers the tap handling process.
        
        Args:
            None

        Returns:
            None
        """
        logger.info('Running main loop')
        with gpiod.request_lines(
                f"/dev/gpiochip{TOUCH_SENSOR_CHIP}",
                consumer="get-line-value",
                config={TOUCH_SENSOR_LINE_OFFSET: gpiod.LineSettings(direction=gpiod.line.Direction.INPUT)},
        ) as request:
            released = True
            while True:
                value = request.get_value(TOUCH_SENSOR_LINE_OFFSET)
                if released:
                    if value == gpiod.line.Value.ACTIVE:
                        logger.info('Touch Sensor Tap Registered')
                        # TODO: Consider threading here
                        self.handle_tap()
                        released = False
                    else:
                        time.sleep(0.05)
                elif value == gpiod.line.Value.INACTIVE:
                    released = True


if __name__ == "__main__":
    logger.info('Starting touch_sensor.py')
    touch_sensor = TouchSensor()
    touch_sensor.run()
