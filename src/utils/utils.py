from enum import Enum
import fcntl
import subprocess
import logging
import os
import json
import time
from typing import Dict, Any

from src.utils.paths import PROJECT_DIR

TIMESTAMP_FORMAT = '%Y-%m-%d %X'

logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])

class SelfReleasingLock:
    def __init__(self, lockfile_path):
        self.lockfile_path = lockfile_path
        self.lockfile = None

    def __enter__(self):
        self.lockfile = open(self.lockfile_path, 'w')
        fcntl.flock(self.lockfile, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.flock(self.lockfile, fcntl.LOCK_UN)
        self.lockfile.close()


class TapStatus(Enum):
    """Represents the status of a tap."""
    GOOD = 0
    BAD = 1

    def __repr__(self):
        return f'{self.value}'

    def to_json(self):
        return self.value

class NFCType(Enum):
    """Represents the type of an NFC Tag."""
    ORDER = 0
    EMPLOYEE = 1

    def __repr__(self):
        return f'{self.value}'

    def to_json(self):
        return self.value


def get_device_id() -> str:
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
