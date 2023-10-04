import datetime
import sys
from zoneinfo import ZoneInfo

# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary

PROGRAM_NAME = None

def set_program_name(program_name):
    global PROGRAM_NAME
    PROGRAM_NAME = program_name

def print_log(format_str, *args):
    """
    Logs messages with a timestamp and program name.

    Args:
        program_name (str): The name of the program or module.
        format_str (str): The format string for the message.
        *args: Variable length argument list to format the string.

    Returns:
        None
    """
    current_time = datetime.datetime.now(ZoneInfo('US/Eastern'))
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

    if format_str.startswith('\n'):
        # add newline before the timestamp
        print(f"\n{timestamp}::{PROGRAM_NAME}::", end='')
        format_str = format_str[1:]  # remove the first character
    else:
        print(f"{timestamp}::{PROGRAM_NAME}::", end='')

    print(format_str.format(*args))


def perror_log(format_str, *args):
    """
    Logs error messages with a timestamp and program name to stderr.

    Args:
        program_name (str): The name of the program or module.
        format_str (str): The format string for the error message.
        *args: Variable length argument list to format the string.

    Returns:
        None
    """
    current_time = datetime.datetime.now(ZoneInfo('US/Eastern'))
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp}::{PROGRAM_NAME}::{format_str.format(*args)}", file=sys.stderr)