#!/usr/bin/python3.9

# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary

# Standard library imports
import time
import requests
import json
import datetime
import sys
import os
import signal
import configparser

# Third-party imports
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from collections import namedtuple
from boto3.dynamodb.conditions import Key, Attr
import numpy as np
import boto3
import netifaces as ni

# Local project libraries
from utility.utils import *
from utility.display_utils import *
from utility.data_utils import *
from utility.log_utils import *
from utility.signal_utils import *

# File Paths
FilePathConstants = namedtuple("FilePathConstants", ["OPERATION_TAPS", "LAST_TAGS_AND_IDS", "FIFO_PATH"])
FILE_PATH_INFO = FilePathConstants(
    OPERATION_TAPS="/var/lib/screen/operation_taps.json",
    LAST_TAGS_AND_IDS="/var/lib/screen/last_tags_and_ids.json",
    FIFO_PATH="/tmp/screenPipe"
)

# Load environment variables
load_dotenv()

# Constants for Airtable configurations
AirtableConstants = namedtuple("AirtableConstants", ["API_KEY"])
AIRTABLE_CONST = AirtableConstants(API_KEY=os.getenv('AIRTABLE_API_KEY'))

# Check for mandatory environment variables
if not AIRTABLE_CONST.API_KEY:
    raise ValueError("'AIRTABLE_API_KEY' is not set.")

# Constants
BATCH_SIZE = 10
TABLE_NAME = "API_Requests"


def pull_last_tags_and_ids(table):
    """
    Update the `last_tags_and_ids` dictionary with data from the database.

    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.

    Returns:
        tuple: A tuple containing two elements:
            - bool: True if the data was successfully retrieved and updated, False otherwise.
            - dict: The updated `last_tags_and_ids` dictionary.
    """
    last_tags_and_ids = load_json_from_file(FILE_PATH_INFO.LAST_TAGS_AND_IDS)
    machine_id = get_machine_id()

    if not last_tags_and_ids.get("machine_record_id"):
        # Define request data for retrieving machine record
        request_data = {
            'table_name': 'tblFOfDowcZNlPRDL',
            'filter_id': 'fldbh9aMmA6qAoNKq',
            'filter_value': machine_id,
            'field_mappings': [
                ("fldZsM3YEVQqpJMFF", "record_id"),
                ("fldfXLG8xbM9S3Evx", "order_tag_record_id"),
                ("fldN0cePGQy8jMkBa", "employee_tag_record_id"),
                ("fldcaeaey2E5R8Iqp", "last_order_tap"),
                ("fldVALQ4NGPNVrvZz", "last_employee_tap"),
                ("fldcFVtGOWbd8RgT6", "order_id"),
                ("fldJQd3TmtxURsQy0", "employee_name")
            ]
        }

        is_push_success, partition_key = push_item_db(table, "GetRecord", request_data)

        if is_push_success:
            is_pull_success, data = pull_item_db(table, partition_key)

            if is_pull_success:
                # Convert data to JSON and extract relevant details
                data_json = json.loads(data['Data'])['Records'][0]
                last_tags_and_ids.update({
                    "machine_record_id": data_json.get('record_id', ' '),
                    "last_order_record_id": data_json.get("order_tag_record_id", " ")[0],
                    "last_employee_record_id": data_json.get("employee_tag_record_id", " ")[0],
                    "last_order_tap": format_utc_to_est(data_json.get("last_order_tap", "")),
                    "last_employee_tap": format_utc_to_est(data_json.get("last_employee_tap", "")),
                    "order_id": data_json.get("order_id", " ")[0],
                    "employee_name": data_json.get("employee_name", " ")[0],
                    "units_employee": 0,
                    "units_order": 0,
                    "last_employee_tag": "None",
                    "last_order_tag": "None"
                })

    return (not is_push_success or not is_pull_success), last_tags_and_ids


def push_local_ip_to_db(table, last_tags_and_ids):
    """
    Pushes the local IP address of the machine to the DynamoDB.

    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
        last_tags_and_ids (dict): A dictionary containing the current tags and IDs.

    Returns:
        bool: True if the IP address was pushed successfully, False otherwise.
    """
    local_ip = get_local_ip()  # Obtain local IP address of the Linux machine on wlan0

    request_data = {
        "local_ip": local_ip,
        "machine_record_id": last_tags_and_ids.get("machine_record_id", "None")
    }

    # Attempt to push data to DynamoDB
    if push_item_db(table, "LocalIPAddress", request_data)[0]:
        print_log(f"Local IP Address pushed successfully: {local_ip}")
        return True
    else:
        return False


def handle_button_tap(table, last_tags_and_ids, operation_taps, current_batch_count, timestamp):
    """
    Handle a button tap event.

    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
        last_tags_and_ids (dict): A dictionary containing the current tags and IDs.
        operation_taps (dict): A dictionary containing the operation taps.
        current_batch_count (int): The current batch count.
        timestamp (str): The timestamp of the button tap.

    Returns:
        tuple: A tuple containing three elements:
            - bool: True if the button tap was handled successfully, False otherwise.
            - dict: The updated `operation_taps` dictionary.
            - int: The updated `current_batch_count`.
    """
    if last_tags_and_ids["last_employee_tag"] != "None" and last_tags_and_ids["last_order_tag"] != "None":
        print_log("Button Pressed")
        # TODO: Make sure timestamp is in correct format with seconds
        request_data = {
            "machine_record_id": last_tags_and_ids["machine_record_id"],
            "employee_tag_record_id": last_tags_and_ids["last_employee_record_id"],
            "order_tag_record_id": last_tags_and_ids["last_order_record_id"],
            "timestamp": timestamp
        }
        operation_taps["Records"].append(request_data)
        current_batch_count += 1
        if current_batch_count >= BATCH_SIZE:
            if not push_item_db(table, "OperationTapEvent", operation_taps):
                return False, operation_taps, current_batch_count
            current_batch_count = 0
            operation_taps = {"Records": []}

        last_tags_and_ids.update({
            "units_order": last_tags_and_ids["units_order"] + 1,
            "units_employee": last_tags_and_ids["units_employee"] + 1
        })
    else:
        return False, operation_taps, current_batch_count

    return True, operation_taps, current_batch_count


def handle_employee_tap(table, last_tags_and_ids, tag_uid, timestamp):
    """
    Handle an NFC tap event for an employee.

    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
        last_tags_and_ids (dict): A dictionary containing the current tags and IDs.
        tag_uid (str): The UID of the NFC tag.
        timestamp (str): The timestamp of the NFC tap.

    Returns:
        bool: True if the employee tap was handled successfully, False otherwise.
    """
    last_employee_record_id_temp = last_tags_and_ids["last_employee_record_id"]
    employee_name_temp = last_tags_and_ids["employee_name"]

    request_data = {
        'table_name': 'tblbRYLt6rr4nTbP6',
        'filter_id': 'fldyYKc2g0dBdolKQ',
        'filter_value': tag_uid,
        'field_mappings': [
            ("fldOYvm4LsaM9pJNw", "employee_name"),
            ("fld49C1CkqgW9hA3p", "record_id")
        ]
    }

    pull_success, employee_record = get_record(table, request_data)

    if not employee_record:
        # TODO: Correct the request data format for creating a record
        # If the employee record is not found, create a new one
        request_data = {
            "table_name": "tblbRYLt6rr4nTbP6",
            "fields": {
                "fldyYKc2g0dBdolKQ": tag_uid,
                "iot_device_field_id": "iot_device_record_id"
            }
        }
        last_tags_and_ids["employee_name"] = "NO NAME"
        employee_record = create_record(table, request_data)
        last_tags_and_ids["last_employee_record_id"] = employee_record["records"][0]["fields"]["Record ID"]
    else:
        # TODO: Confirm format of timestamp
        # Update the last_tags_and_ids with the pulled employee data
        last_tags_and_ids.update({
            "employee_name": employee_record["employee_name"][0],
            "last_employee_record_id": employee_record["record_id"],
            "last_employee_tap": timestamp,
            "units_order": 0,
            "units_employee": 0
        })

    request_data = {
        "machine_record_id": [last_tags_and_ids["machine_record_id"]],
        "employee_tag_record_id": [last_tags_and_ids["last_employee_record_id"]]
    }

    push_success = push_item_db(table, "EmployeeNFC", request_data)

    if not push_success:
        last_tags_and_ids.update({
            "last_employee_record_id": last_employee_record_id_temp,
            "employee_name": employee_name_temp
        })
        return False

    last_tags_and_ids.update({
        "last_employee_tag": tag_uid,
        "last_employee_tap": timestamp,
        "units_order": 0,
        "units_employee": 0
    })

    return True


def handle_nfc_tap(table, last_tags_and_ids, tag_uid, timestamp):
    """
    Handle an NFC tap event, distinguishing between employee and order tags.

    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
        last_tags_and_ids (dict): A dictionary containing the current tags and IDs.
        tag_uid (str): The UID of the NFC tag.
        timestamp (str): The timestamp of the NFC tap.

    Returns:
        bool: True if the NFC tap was handled successfully, False otherwise.
    """
    request_data = {
        'table_name': 'tbl6vse0gHkuPxBaT',
        'filter_id': 'fldRHuoXAQr4BF83j',
        'filter_value': tag_uid,
        'field_mappings': [
            ("fldRi8wjAdfBkDhH8", "record_id"),
            ("fldSrxknmVrsETFPx", "order_id")
        ]
    }

    pull_success, order_record = get_record(table, request_data)

    if not order_record:
        return handle_employee_tap(table, last_tags_and_ids, tag_uid, timestamp)

    if last_tags_and_ids["last_employee_record_id"] == "None":
        return False

    # Update the last_tags_and_ids with the pulled order data
    last_tags_and_ids.update({
        "last_order_record_id": order_record["record_id"],
        "last_order_tag": tag_uid,
        "last_order_tap": timestamp,
        "units_order": 0,
        "order_id": "None" if order_record["order_id"] == "None" else order_record["order_id"][0]
    })

    request_data = {
        "machine_record_id": [last_tags_and_ids["machine_record_id"]],
        "order_tag_record_id": [last_tags_and_ids["last_order_record_id"]],
        "employee_tag_record_id": [last_tags_and_ids["last_employee_record_id"]]
    }

    if not push_item_db(table, "OrderNFC", request_data):
        return False

    return True


def main():
    # Initialize signal handlers
    initialize_signal_handlers(["SIGTERM"])

    # Read the Airtable API Key
    airtable_config = configparser.ConfigParser()
    airtable_config.read("/home/potato/.airtable/credentials.txt")

    # Load AWS credentials from the file
    aws_config = configparser.ConfigParser()
    aws_config.read("/home/potato/.aws/credentials.txt")
    aws_access_key_id = aws_config.get("Credentials", "aws_access_key_id")
    aws_secret_access_key = aws_config.get("Credentials", "aws_secret_access_key")

    # Initialize DynamoDB resource with the credentials
    dynamodb = boto3.resource(
        "dynamodb",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name="us-east-1"
    )
    table = dynamodb.Table(TABLE_NAME)

    # Print initialization logs
    print_log("Starting Screen.py")
    print_log("Pulling Previous Data")

    # Push the latest local ip to the database
    is_push_success = push_local_ip_to_db(table, last_tags_and_ids)
    if not is_push_success:
        perror_log("Failed to push local ip address to AWS database")
        sys.exit(0)

    # Pull the last set of tags and IDs from the database
    is_update_success, last_tags_and_ids = pull_last_tags_and_ids(table)
    if not is_update_success:
        perror_log("Failed to update last_tags_and_ids from AWS database")
        sys.exit(0)

    # Load batched button presses from a file
    operation_taps = load_json_from_file(FILE_PATH_INFO.OPERATION_TAPS, default_value={"Records": []})

    # Update the current batch count based on the loaded tap data
    current_batch_count = len(operation_taps["Records"])

    print_log("Starting Display")

    # Initialize the display manager
    display_manager = DisplayManager()

    try:
        while True:
            time.sleep(0.25)
            tap_success = True

            # Display the relevant data on the screen
            display_manager.draw_display(last_tags_and_ids)

            # Read data from the FIFO Pipe
            fifo_data = read_from_file(FILE_PATH_INFO.FIFO_PATH)
            if not fifo_data:
                continue

            fifo_data_split = fifo_data.split("::")
            program_name = fifo_data_split[0]

            # Handle operation taps
            if program_name == "operation_tap_listener.c":
                timestamp = fifo_data_split[1]
                push_success, operation_taps, current_batch_count = handle_button_tap(
                    table,
                    last_tags_and_ids,
                    operation_taps,
                    current_batch_count,
                    timestamp
                )
                if not push_success:
                    perror_log(f"Error: Operation taps not registered \n FIFO Data: {fifo_data}")
                    tap_success = False
                save_json_to_file(FILE_PATH_INFO.OPERATION_TAPS, operation_taps)

            # Handle NFC taps
            elif program_name == "nfc_tap_listener.c":
                tag_uid = fifo_data_split[1].lower()
                timestamp = fifo_data_split[2]
                if not handle_nfc_tap(table, last_tags_and_ids, tag_uid, timestamp):
                    perror_log(f"Error: NFC tap not registered \n FIFO Data: {fifo_data}")
                    tap_success = False

            # Handle invalid program names
            else:
                perror_log(f"Error: invalid program name \n FIFO Data: {fifo_data}")

            # Save the last tags and IDs to a file
            save_json_to_file(FILE_PATH_INFO.LAST_TAGS_AND_IDS, last_tags_and_ids)

            # Update the display with the background color indicating success or failure
            bg_color = (0, 170, 0) if tap_success else (0, 0, 255)
            display_manager.draw_display(last_tags_and_ids, bg_color=bg_color)

    except KeyboardInterrupt:
        print_log("Program Interrupted")


if __name__ == "__main__":
    main()
