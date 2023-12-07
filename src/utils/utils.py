import subprocess
import time
import os


TIMESTAMP_FORMAT = '%Y-%m-%d %X'


def __get_device_id() -> str:
    """Retrieve the device ID from a Unix-like file system.

    This function is implemented to avoid errors when referencing Unix-like file
    structure on Windows computers.

    Returns:
        str: The device ID if the file exists, otherwise an empty string.
    """
    device_id = ''
    if os.path.exists('/etc/machine-id'):
        device_id = subprocess.check_output('cat /etc/machine-id', shell=True)
    return device_id


DEVICE_ID = __get_device_id()


def ftimestamp(timestamp: float) -> str:
    return time.strftime(TIMESTAMP_FORMAT, time.localtime(timestamp))