from enum import Enum
import fcntl


TIMESTAMP_FORMAT = '%Y-%m-%d %X'

class FileLock:
    def __init__(self, lock_file, timeout):
        self.lock_file = lock_file
        self.timeout = timeout
        self.fd = None

    def _is_lock_stale(self):
        try:
            with open(self.lock_file, 'r') as file:
                timestamp = float(file.read())
                return (time.time() - timestamp) > self.timeout
        except FileNotFoundError:
            return True
        except ValueError:
            return True

    def acquire(self):
        self.fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR)
        while True:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Lock acquired, update the timestamp
                os.write(self.fd, str(time.time()).encode())
                break
            except OSError as e:
                if e.errno == errno.EACCES or e.errno == errno.EAGAIN:
                    if self._is_lock_stale():
                        self.release()  # Release stale lock
                else:
                    raise

    def release(self):
        if self.fd is not None:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

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

def get_machine_id() -> str:
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