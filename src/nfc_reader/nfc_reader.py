import json
import os
import logging
import logging.config
import time

from ctypes import CDLL, c_bool, c_char_p, c_size_t, create_string_buffer
from src.cloud_db.cloud_db import CloudDBClient
from src.utils.nfc_reader_utils import NFCTag
from src.utils.paths import (NFC_READER_TO_SCREEN_PIPE, PROJECT_DIR)
from src.utils.utils import NFCType, get_device_id

logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])


class NFCReader:
    """Represents an NFC Reader.

    Attributes:
        cloud_db: An instance of CloudDBClient for database interactions.
    """

    def __init__(self) -> None:
        """
        Initializes the NFC Reader with Supabase client.

        """
        self.cloud_db = CloudDBClient()
        self.lib = self.init_poll()
        self.device_id = get_device_id()


    def handle_nfc_tap(self, uid) -> None:
        """Handles a tap event.

        The method records the tap event, looks up the unique ID in the cloud database 
        and then sends the result the screen FIFO if it is a valid unique ID.
            
        """
        timestamp = time.time()
        logger.info(
            f"Device Id: {self.device_id}, \
              Timestamp: {timestamp}, \
              NFC ID: {uid}"
        )
        result = self.cloud_db.lookup_uid(uid)
        if result.type == NFCType.EMPLOYEE:
            self.cloud_db.insert_employee_tap(result)
        if result.type == NFCType.ORDER:
            self.cloud_db.insert_order_tap(result)
        logger.info(f"Lookup Result Value: {result.data}, \
                    Type: {result.type}"                                        )
        self.pipe_nfc_data(result)

    def pipe_nfc_data(self, tag) -> None:
        """Sends NFC tag lookup results to named pipe for IPC with screen module.

        Args:
            lookup_result: A string containing the lookup_result from tapping a NFC tag.
        
        Raises:
            FileNotFoundError: If the pipeline path does not exist.
        """
        logger.info('Sending NFC lookup result to screen')
        nfc_data = dict(tag)
        try:
            with open(NFC_READER_TO_SCREEN_PIPE, 'a') as pipeout:
                json.dump(nfc_data, pipeout)
                pipeout.write('\n')
                pipeout.flush()
        except FileNotFoundError:
            logger.error('Named pipe not found')
            raise FileNotFoundError('Named pipe not found')
        except BrokenPipeError:
            logger.error('Cannot write to pipe - broken pipe')
        except Exception as e:
            logger.error(f"Error writing to pipe: {e}")

    def init_poll(self):
        """
        Initializes and returns a CDLL object for interacting with the 'libpoll.so' shared library.

        Sets the argument types and return type for the 'poll' function within the shared library.
        
        Returns:
            CDLL: Configured library object ready to use for calling the 'poll' function.
        """
        lib = CDLL("./libpoll.so")
        lib.poll.argtypes = [c_char_p, c_size_t]
        lib.poll.restype = None
        lib.is_tag_present.argtypes = None
        lib.is_tag_present.restype = c_bool
        return lib

    def run(self) -> None:
        """Monitors the polling function for tap events and processes them.

        Continuously runs a C function to check for NFC taps. If a tap is detected,
        interprets it as a tap event and triggers the tap handling process.
        """
        logger.info('Running main loop')
        uid_len = 64  # Define the buffer size for the UID string
        while True:
            uid_buf = create_string_buffer(uid_len)  # Create a buffer for the UID
            self.lib.poll(uid_buf, uid_len)  # Call the C function to fill the buffer with the UID string
            uid_str = uid_buf.value.decode('utf-8')
            self.handle_tap(uid_str)
            while self.lib.is_tag_present():
                pass
            logger.info("Tag has been removed.")


if __name__ == "__main__":
    logger.info('Starting nfc_reader.py')
    nfc_reader = NFCReader()
    nfc_reader.run()
