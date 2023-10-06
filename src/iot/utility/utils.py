import datetime
from zoneinfo import ZoneInfo
import netifaces as ni


# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary


def get_machine_id():
    """
    Retrieves the machine ID from the system.

    Returns:
        str: The machine ID or None if not found.
    """
    machine_id_paths = ["/etc/machine-id", "/var/lib/dbus/machine-id"]

    for path in machine_id_paths:
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            continue
    return None


def get_local_ip(interface='wlan0'):
    """
    Retrieves the local IP address of the specified interface.

    Args:
        interface (str): The network interface to check. Default is 'wlan0'.

    Returns:
        str: The IP address or 'UNKNOWN' if not found.
    """
    try:
        ip = ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
    except (KeyError, ValueError):
        ip = 'UNKNOWN'  # TODO: Is there a reason why 'UNKNOWN' is returned instead of None?
    return ip


def format_utc_to_est(date_str):
    """
    Converts a UTC datetime string to EST and formats it.

    Args:
        date_str (str): The UTC datetime string.

    Returns:
        str: The formatted EST datetime string or an empty string if date_str is invalid.
    """
    if not date_str or date_str == "None":
        return ""
    
    date_str = date_str.replace('Z', '')
    
    try:
        date_utc = datetime.datetime.fromisoformat(date_str).astimezone(datetime.timezone.utc)
    except ValueError:
        return ""
    
    date_est = date_utc.astimezone(ZoneInfo('America/New_York'))
    return date_est.strftime('%Y-%m-%d %l:%M %p')


def get_current_time(format_seconds=True):
    """
    Retrieves the current time in EST.

    Args:
        format_seconds (bool): Whether to include seconds in the format.

    Returns:
        str: The formatted EST datetime string.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_est = now_utc.astimezone(ZoneInfo('America/New_York'))
    if format_seconds:
        return now_est.strftime('%Y-%m-%d %l:%M:%S %p')
    return now_est.strftime('%Y-%m-%d %l:%M %p')
