import subprocess
import time

DEVICE_ID = subprocess.check_output('cat /etc/machine_id', shell=True)

TIMESTAMP_FORMAT = '%Y-%m-%d %X'


def ftimestamp(timestamp: float) -> str:
    return time.strftime(TIMESTAMP_FORMAT, time.localtime(timestamp))