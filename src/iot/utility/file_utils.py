import json
import time
from log_utils import *
from utils import *

# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary


def read_from_file(file_path):
    """
    Reads data from a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(file_path, "r") as f:
        return f.read()


def save_json_to_file(file_path, data):
    """
    Saves the provided JSON data to a file.

    Args:
        file_path (str): The path of the file where the data will be saved.
        data (dict): A dictionary containing the data to save.

    Returns:
        bool: True if the data was successfully saved, False otherwise.
    """
    try:
        json_str = json.dumps(data)  # This might raise a TypeError if data can't be serialized to JSON
        with open(file_path, 'w') as file:
            file.write(json_str)
        return True
    except TypeError:
        perror_log(f"Error: Provided data cannot be serialized to JSON \n Data: {json_str}")
        return False


def load_json_from_file(file_path, default_value=None):
    """
    Loads JSON data from a file.

    Args:
        file_path (str): The path of the file from which the data will be loaded.
        default_value (dict, optional): Default value to return if the file is not found or contains invalid data.

    Returns:
        dict: The loaded data or the default_value if not found or if the data is invalid.
    """
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        perror_log(f"Error: File {file_path} not found.")
    except json.JSONDecodeError:
        perror_log(f"Error: The content of {file_path} is not valid JSON.")
    return default_value