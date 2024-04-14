from enum import Enum
import fcntl
import subprocess
import logging
import os
import time
from typing import Self, Optional, Dict, Any
import json

from src.utils.paths import PROJECT_DIR

TIMESTAMP_FORMAT = '%Y-%m-%d %X'

logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])


class SelfReleasingLock:
    """Represents a lock that automatically releases itself when the context manager exits or when it is old.

    Attributes:
        lock_file_path: The path to the lock file.
        lock_file: The file object representing the lock file.
        max_age: The maximum age (in seconds) of the lock file.
    """

    def __init__(self, lock_file_path: str, max_age: int = 60) -> None:
        """Initializes the SelfReleasingLock with the specified lock file path and max age.

        Args:
            lock_file_path: The path to the lock file.
            max_age: The maximum age (in seconds) of the lock file.

        Returns:
            None
        """
        self.lock_file_path = lock_file_path
        self.lock_file = None
        self.max_age = max_age

    def __enter__(self) -> Self:
        """Acquires the lock and returns the SelfReleasingLock object.
        
        Args:
            None
        
        Returns:
            The SelfReleasingLock object.
        """
        if not os.path.exists(self.lock_file_path):
            os.makedirs(os.path.dirname(self.lock_file_path), exist_ok=True)
            open(self.lock_file_path, 'w').close()
            logger.warning(f"Created lock file {self.lock_file_path} since it did not exist.")

        while not self.is_lock_old():
            logger.warning(f"Waiting for lock on {self.lock_file_path}...")
            time.sleep(1)

        logger.warning(f"Lock file {self.lock_file_path} is older than {self.max_age} seconds. \
            Assuming it was left behind by a previous process."                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      )

        self.__exit__(None, None, None)
        self.lock_file = open(self.lock_file_path, 'w')
        fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Releases the lock when the context manager exits.
        
        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The exception traceback.
        
        Returns:
            None
        """
        if self.lock_file:
            fcntl.flock(self.lock_file, fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_file = None
        else:
            logger.warning(f"Reaching __exit__ without acquiring lock for {self.lock_file_path}.")

    def is_lock_old(self) -> bool:
        """Checks if a file is older than the max age (in seconds).
        
        Args:
            None

        Returns:
            True if the lock is older than the max age, False otherwise.
        """
        if not os.path.exists(self.lock_file_path):
            return False
        return time.time() - os.path.getmtime(self.lock_file_path) > self.max_age


class TapStatus(Enum):
    """Represents the status of a tap.
    
    Attributes:
        GOOD: A tap that is valid.
        BAD: A tap that is invalid.
    """
    GOOD = 0
    BAD = 1

    def __repr__(self) -> str:
        """Returns the string representation of the TapStatus object.
        
        Args:
            None
        
        Returns:
            A string representing the TapStatus object.
        """
        return f"{self.value}"

    def to_json(self) -> str:
        """Returns the JSON representation of the TapStatus object.

        Args:
            None

        Returns:
            A string representing the JSON representation of the TapStatus object.
        """
        return self.value

class NFCType(Enum):
    """Represents the type of an NFC Tag."""
    ORDER = 0
    EMPLOYEE = 1

    def __repr__(self) -> str:
        """Returns the string representation of the TapStatus object.
        
        Args:
            None
        
        Returns:
            A string representing the TapStatus object.
        """
        return f"{self.value}"

    def to_json(self) -> str:
        """Returns the JSON representation of the TapStatus object.

        Args:
            None

        Returns:
            A string representing the JSON representation of the TapStatus object.
        """
        return self.value

class NFCType(Enum):
    """Represents the type of an NFC Tag."""
    ORDER = 0
    EMPLOYEE = 1

    def __repr__(self):
        return f'{self.value}'

    def to_json(self):
        return self.value


def get_device_id() -> Optional[str]:
    """Retrieves the device's hostname and uses it as a device ID.

    Returns:
        A string representing the device's hostname, used as a device ID.

    Raises:
        subprocess.CalledProcessError: If the 'hostname' command fails.
    """
    try:
        process = subprocess.run(['hostname'], capture_output=True, text=True, check=True)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred while fetching the hostname: {e}")
        return None


def is_at_least_next_day(from_timestamp: float, to_timestamp: float) -> bool:
    """Check if the 'to_timestamp' is at least the next day compared to 'from_timestamp'.

    Args:
        from_timestamp (float): The starting Unix timestamp.
        to_timestamp (float): The ending Unix timestamp.

    Returns:
        bool: True if 'to_timestamp' is at least the next day from 'from_timestamp', False otherwise.
    """
    day_in_seconds = 86400
    # Get the start of the day for both timestamps
    from_day_start = from_timestamp - (from_timestamp % day_in_seconds)
    to_day_start = to_timestamp - (to_timestamp % day_in_seconds)

    # Check if to_timestamp is at least the next day from from_timestamp
    return to_day_start > from_day_start


def read_device_state(path_to_device_state: str) -> Dict[str, Any]:
    """Read the device state from a JSON file.

    Args:
        path_to_device_state (str): Path to the JSON file containing the device state.

    Returns:
        Dict[str, Any]: A dictionary representing the device state.
    
    Raises:
        FileNotFoundError: If the specified JSON file path does not exist.
        JSONDecodeError: If there is an error decoding the JSON data from the file.
    """
    logger.info('Reading device state')
    try:
        with open(path_to_device_state, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error('Device state file not found')
        raise FileNotFoundError
    except json.JSONDecodeError:
        logger.error('Unable to parse device state: Invalid JSON format')
        raise json.JSONDecodeError


def write_device_state(device_state: Dict[str, Any], path_to_device_state: str) -> None:
    """Write the updated device state to a JSON file.

    Args:
        device_state (Dict[str, Any]): The device state to write.
        path_to_device_state (str): Path to the JSON file where the device state will be saved.
    
    Raises:
        FileNotFoundError: If the specified JSON file path does not exist.
        IOError: If there is an error writing to the file.
    """
    logger.info('Writing device state')
    device_state['saved_timestamp'] = time.time()
    try:
        with open(path_to_device_state, 'w') as file:
            json.dump(device_state, file, indent=4)
    except FileNotFoundError:
        logger.error('Device state file not found')
        raise FileNotFoundError  # TODO: Determine error message format
    except IOError as e:
        logger.error(f"An error occurred while writing to device state: {e}")
        raise IOError  # TODO: Determine error message format
