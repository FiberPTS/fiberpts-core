import json
import os
import logging
import logging.config
import time

from src.nfc_reader.poll import poll
from src.cloud_db.cloud_db import CloudDBClient
from src.utils.paths import (NFC_READER_TO_SCREEN_PIPE, PROJECT_DIR)
from src.utils.utils import get_device_id, TapStatus

logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])

class NFCReader:
    """Represents a NFC Reader.

    Attributes:
        debounce_time: Minimum time interval (in seconds) to consider consecutive taps as distinct.
        screen_pipe: File path to the FIFO used for IPC with the screen module.
        cloud_db: An instance of CloudDBClient for database interactions.
    """

    def __init__(self,
                 debounce_time: int = DEBOUNCE_TIME,
                 screen_pipe: str = NFC_READER_TO_SCREEN_PIPE) -> None:
        """
        Initializes the NFC Reader with specified debounce time and pipe path.

        Args:
            debounce_time: An integer specifying the debounce time in seconds.
            screen_pipe: File path to the screen FIFO.
        """
        self.debounce_time = debounce_time
        self.screen_pipe = screen_pipe
        self.cloud_db = CloudDBClient()
        self.last_tap = 0.0


    def handle_tap(self, tag_id) -> bool:
        """Handles a tap event.

        The method records the tap event, validates it based on the debounce time,
        looks up the tag_id in the cloud database and then sends the result the screen FIFO.

        Returns:
            A boolean indicating whether the tap was valid (True) or not (False).
        """
        timestamp = time.time()
        tap_status = TapStatus.BAD

        if (timestamp - self.last_tap) >= self.debounce_time:
            tap_status = TapStatus.GOOD

        logger.info(
            f"NFC Id: {self.device_id}, \
              Timestamp: {timestamp}, \
              Is Valid: {tap_status == TapStatus.GOOD}"
        )

        is_valid_tap = tap_status == TapStatus.GOOD
        if is_valid_tap:
            result = self.cloud_db.lookup_tag(tag_id)

        self.pipe_tap_data(result)
        self.last_tap = timestamp
        return is_valid_tap

    def pipe_tap_data(self, lookup_result) -> None:
        """Sends NFC tag lookup results to named pipe for IPC with screen module.

        Args:
            lookup_result: A string containing the lookup_result from tapping a NFC tag.
        
        Raises:
            FileNotFoundError: If the pipeline path does not exist.
        """
        logger.info('Sending NFC lookup result to screen')
        try:
            with open(self.screen_pipe, 'a') as pipeout:
                pipeout.write(lookup_result)
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
        """Monitors the polling function for tap events and processes them.

        Continuously runs a C function to check for NFC taps. If a tap is detected,
        interprets it as a tap event and triggers the tap handling process.
        """
        logger.info('Running main loop')
        while True:
            tag_id = poll()
            self.handle_tap(tag_id)


if __name__ == "__main__":
    logger.info('Starting nfc_reader.py')
    nfc_reader = NFCReader()
    nfc_reader.run()

