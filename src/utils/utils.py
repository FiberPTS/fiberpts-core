from enum import Enum
import fcntl
import subprocess
import logging
import os

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
