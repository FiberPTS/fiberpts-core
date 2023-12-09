# Standard library imports
import json
import os
import time
from typing import Dict, Any

# Third-party imports
from PIL import Image
import numpy as np


SAVED_TIMESTAMP_FORMAT = '%Y-%m-%d'

# TODO: Time seems to be 1 day ahead, so we need to identity the issue and fix this.
# TODO: This is duplicate code from utils.py, but I need a specific timestamp format
def ftimestamp(timestamp: float) -> str:
    """
    Format a given Unix timestamp into a string based on the predefined timestamp format.

    Args:
        timestamp (float): The Unix timestamp to format.

    Returns:
        str: The formatted timestamp as a string.
    """
    return time.strftime(SAVED_TIMESTAMP_FORMAT, time.localtime(timestamp))


def is_at_least_next_day(from_timestamp: float, to_timestamp: float) -> bool:
    """
    Check if the 'to_timestamp' is at least the next day compared to 'from_timestamp'.

    Args:
        from_timestamp (float): The starting Unix timestamp.
        to_timestamp (float): The ending Unix timestamp.

    Returns:
        bool: True if 'to_timestamp' is at least the next day from 'from_timestamp', False otherwise.
    """
    # Get the start of the day for both timestamps
    from_day_start = from_timestamp - (from_timestamp % 86400)
    to_day_start = to_timestamp - (to_timestamp % 86400)

    # Check if to_timestamp is at least the next day from from_timestamp
    return to_day_start > from_day_start


def read_device_state(path_to_device_state: str) -> Dict[str, Any]:
    """
    Read the device state from a JSON file. Reset the unit count if the saved timestamp is from the previous day.

    Args:
        path_to_device_state (str): Path to the JSON file containing the device state.

    Returns:
        Dict[str, Any]: A dictionary representing the device state.
    
    Raises:
        FileNotFoundError: If the specified JSON file path does not exist.
        JSONDecodeError: If there is an error decoding the JSON data from the file.
    """
    try:
        with open(path_to_device_state, 'r') as file:
            device_state = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError # TODO: Determine error message format
    except json.JSONDecodeError:
        raise json.JSONDecodeError # TODO: Determine error message format
    saved_timestamp = device_state['saved_timestamp']
    current_time = time.time()

    if is_at_least_next_day(saved_timestamp, current_time):
            device_state['unit_count'] = 0
            write_device_state(device_state, path_to_device_state)

    return device_state


def write_device_state(device_state: Dict[str, Any], path_to_device_state: str) -> None:
    """
    Write the updated device state to a JSON file.

    Args:
        device_state (Dict[str, Any]): The device state to write.
        path_to_device_state (str): Path to the JSON file where the device state will be saved.
    
    Raises:
        FileNotFoundError: If the specified JSON file path does not exist.
        IOError: If there is an error writing to the file.
    """
    device_state['saved_timestamp'] = time.time()
    try:
        with open(path_to_device_state, 'w') as file:
            json.dump(device_state, file, indent=4)
    except FileNotFoundError:
        raise FileNotFoundError # TODO: Determine error message format
    except IOError as e:
        raise IOError # TODO: Determine error message format


def read_pipe(path_to_pipe: str) -> Dict[str, Any]:
    """
    Read and parse JSON data from a named pipe.

    Args:
        path_to_pipe (str): Path to the named pipe.

    Returns:
        Dict[str, Any]: A dictionary containing the parsed data from the pipe.

    Raises:
        FileNotFoundError: If the named pipe does not exist.
    """
    try:
        fd = os.open(path_to_pipe, os.O_RDONLY | os.O_NONBLOCK)
    except FileNotFoundError:
        raise FileNotFoundError # TODO: Determine error message format
    else:
        with os.fdopen(fd, 'r') as pipein:
            raw_data = pipein.read()
        if raw_data:
            return json.loads(raw_data)
        return {}


def image_to_raw_rgb565(image: Image) -> np.ndarray:
    """
    Convert a PIL image to raw RGB565 format.

    Args:
        image (Image): The PIL image to convert.

    Returns:
        np.ndarray: A numpy array containing the image data in RGB565 format.
    """
    # Split into R, G, B channels
    r, g, b = image.split()
    # Convert each channel to an appropriate numpy array
    r = np.array(r, dtype=np.uint16)
    g = np.array(g, dtype=np.uint16)
    b = np.array(b, dtype=np.uint16)
    # Right shift to fit into 565 format
    r >>= 3  # Keep top 5 bits
    g >>= 2  # Keep top 6 bits
    b >>= 3  # Keep top 5 bits
    # Combine into RGB 565 format
    rgb565 = (r << 11) | (g << 5) | b
    # Convert the 2D array to a 1D array (raw data)
    raw_rgb565 = rgb565.ravel()
    return raw_rgb565


def write_image_to_fb(image: Image, path_to_fb: str) -> None:
    """
    Write a PIL image to a framebuffer device in RGB565 format.

    Args:
        image (Image): The PIL image to write.
        path_to_fb (str): Path to the framebuffer device.
    
    Raises:
        FileNotFoundError: If the framebuffer device path does not exist.
        IOError: If there is an error writing to the framebuffer.
    """
    raw_data = image_to_raw_rgb565(image)
    try:
        with open(path_to_fb, "wb") as f:
            f.write(raw_data.tobytes())
    except FileNotFoundError:
        raise FileNotFoundError # TODO: Determine error message format
    except IOError as e:
        raise IOError # TODO: Determine error message format
