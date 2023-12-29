from enum import Enum
import fcntl


TIMESTAMP_FORMAT = '%Y-%m-%d %X'

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
    """Retrieves the unique ID of the device running this program.

    This function specifically targets Unix-like systems. To ensure
    compatibility with non-Unix systems, it returns an empty string.

    Returns:
        str: The device ID if the file exists, otherwise an empty string.
    """
    try:
        with open('/etc/machine-id', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return ''