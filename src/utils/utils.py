import subprocess
import time
import os


TIMESTAMP_FORMAT = '%Y-%m-%d %X'


def __get_machine_id() -> str:
    """Retrieves the unique ID of the machine running this program.

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


DEVICE_ID = __get_machine_id()


def ftimestamp(timestamp: float) -> str:
    return time.strftime(TIMESTAMP_FORMAT, time.localtime(timestamp))