import signal
import sys
import time

# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary

# Global variable to track if a signal interruption has occurred
interrupted = False

# Global variable to store the cleanup function
cleanup_fn = None

def init_signal_handlers(options, fn=None):
    """
    Initialize specific signal handlers based on the provided options.

    Args:
        options (list): A list of signal names to handle, e.g., ['SIGINT', 'SIGTERM'].
        fn (function): The cleanup function to register to be called when signals are caught.

    Returns:
        None
    """
    global cleanup_fn
    cleanup_fn = fn

    signal_mapping = {
        'SIGINT': handle_sigint,
        'SIGUSR1': handle_sigusr1,
        'SIGTERM': handle_sigint
    }

    for opt, handler in signal_mapping.items():
        if opt in options:
            signal.signal(getattr(signal, opt), handler)
            

def handle_sigint(sig, frame):
    """
    Signal handler for SIGINT (e.g., from Ctrl+C).
    Sets the interrupted flag, cleans up if necessary, and exits the program.

    Args:
        sig (int): The signal number.
        frame: Not used but required by signal handlers.

    Returns:
        None
    """
    global interrupted
    interrupted = True
    if cleanup_fn:  # Check if a cleanup function has been registered
        cleanup_fn()  # Call the registered cleanup function
    sys.exit(0)

def handle_sigusr1(sig, frame):
    """
    Signal handler for SIGUSR1. Currently does nothing but can be customized as needed.

    Args:
        sig (int): The signal number.
        frame: Not used but required by signal handlers.

    Returns:
        None
    """
    pass

def sleep_interruptible(ms):
    """
    Sleeps for a specified number of milliseconds, but can be interrupted early if the interrupted flag is set.

    Args:
        ms (int): The number of milliseconds to sleep.

    Returns:
        None
    """
    for _ in range(ms):
        time.sleep(0.001)  # Sleep for 1 millisecond
        if interrupted:  # Check if a signal has been received
            break
