#!/usr/bin/python3.9
# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from collections import namedtuple
from boto3.dynamodb.conditions import Key, Attr
import numpy as np
import time
import requests
import json
import datetime
import sys
import os
import signal
import boto3
import configparser
import netifaces as ni

FilePathConstants = namedtuple("FilePathConstants", ["OPERATION_TAPS", "LAST_TAGS_AND_IDS", "FIFO_PATH"])

AirtableConstants = namedtuple("AirtableConstants", ["API_KEY"])

FILE_PATH_INFO = FilePathConstants(
    OPERATION_TAPS="/var/lib/screen/operation_taps.json",
    LAST_TAGS_AND_IDS="/var/lib/screen/last_tags_and_ids.json",
    FIFO_PATH="/tmp/screenPipe"
)

load_dotenv()

AIRTABLE_CONST = AirtableConstants(
    API_KEY=os.getenv('AIRTABLE_API_KEY')
)

if not AIRTABLE_CONST.API_KEY:
    raise ValueError("'AIRTABLE_API_KEY' is not set.")

# Constants
BATCH_SIZE = 10

def update_last_tags_and_ids(table):
    """
    Update the `last_tags_and_ids` dictionary with data from the database.
    
    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
    
    Returns:
        tuple: A tuple containing two elements:
            - bool: True if the data was successfully retrieved and updated, False otherwise.
            - dict: The updated `last_tags_and_ids` dictionary.
    """
    # Load the last tags, ids, and taps from file
    last_tags_and_ids = load_json_from_file(FILE_PATH_INFO.LAST_TAGS_AND_IDS)
    machine_id = get_machine_id()
    if not last_tags_and_ids.get("machine_record_id"):
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
    return (not is_push_success or not is_push_success), last_tags_and_ids

def push_local_ip_to_db(table, last_tags_and_ids):
    """
    Pushes the local IP address of the machine to the DynamoDB.

    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
        last_tags_and_ids (dict): A dictionary containing the current tags and IDs.

    Returns:
        bool: True if the IP address was pushed successfully, False otherwise.
    """
    # Obtain local IP address of the Linux machine on wlan0
    local_ip = get_local_ip()

    # Prepare request data with local IP and machine_record_id
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


def handle_employee_tap(table, last_tags_and_ids, tag_uid, timestamp):
    last_employee_record_id_temp = last_tags_and_ids["last_employee_record_id"]
    employee_name_temp = last_tags_and_ids["employee_name"]

    field_ids = [("fldOYvm4LsaM9pJNw", "employee_name"), ("fld49C1CkqgW9hA3p", "record_id")]
    employee_dict = get_record("appZUSMwDABUaufib", "tblbRYLt6rr4nTbP6", field_ids, "fldyYKc2g0dBdolKQ", tagId)

    if employee_dict:
        last_tags_and_ids.update({
            "employee_name": employee_dict["employee_name"][0],
            "last_employee_record_id": employee_dict["record_id"]
        })
    else:
        last_tags_and_ids["employee_name"] = tagId
        field_data = {"fldyYKc2g0dBdolKQ": tagId}
        tag_record = create_record("appZUSMwDABUaufib", "tblbRYLt6rr4nTbP6", field_data)
        last_tags_and_ids["last_employee_record_id"] = tag_record["records"][0]["fields"]["Record ID"]

    request_data = {
        "machine_record_id": [last_tags_and_ids["machine_record_id"]],
        "employee_tag_record_id": [last_tags_and_ids["last_employee_record_id"]]
    }
    if not push_item_db(dynamodb, "EmployeeNFC", request_data):
        last_tags_and_ids.update({
            "last_employee_record_id": last_employee_record_id_temp,
            "employee_name": employee_name_temp
        })
        return True  # tap_success

    last_tags_and_ids.update({
        "last_employee_tag": tagId,
        "last_employee_tap": formatted_time,
        "units_order": 0,
        "units_employee": 0
    })
    return False  # tap_success

def handle_nfc_tap(table, fifo_data, last_tags_and_ids):
    tag_uid = fifo_data_split[1].lower()
    timestamp = fifo_data_split[2]
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

    last_tags_and_ids.update({
        "last_order_record_id": order_record["record_id"],
        "last_order_tag": tag_uid,
        "last_order_tap": timestamp,
        "units_order": 0,
        "order_id": "None" if order_record["order_id"] == "None" else order_dict["order_id"][0]
    })

    request_data = {
        "machine_record_id": [last_tags_and_ids["machine_record_id"]],
        "order_tag_record_id": [last_tags_and_ids["last_order_record_id"]],
        "employee_tag_record_id": [last_tags_and_ids["last_employee_record_id"]]
    }

    if not push_item_db(dynamodb, "OrderNFC", request_data):
        return False

    return True

def main():
    initialize_signal_handlers(["SIGTERM"])
    
    # Reading Airtable API Key
    airtable_config = configparser.ConfigParser()
    airtable_config.read("/home/potato/.airtable/credentials.txt")

    # Load AWS credentials from file
    aws_config = configparser.ConfigParser()
    aws_config.read("/home/potato/.aws/credentials.txt")

    aws_access_key_id = aws_config.get("Credentials", "aws_access_key_id")
    aws_secret_access_key = aws_config.get("Credentials", "aws_secret_access_key")

    dynamodb = boto3.resource(
        "dynamodb",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name="us-east-1"
    )

    table = dynamodb.Table(table_name)
    
    print_log("Starting Screen.py")
    print_log("Pulling Previous Data")

    is_update_success, last_tags_and_ids = update_last_tags_and_ids(table, machine_id, last_tags_and_ids)
    if not is_update_success:
        perror_log("Failed to update last_tags_and_ids from AWS database")
        sys.exit(0)

    # Load the batched button presses from file
    operation_taps = load_json_from_file(FILE_PATH_INFO.OPERATION_TAPS, default_value={"Records": []})
    
    is_push_success = push_local_ip_to_db(table, last_tags_and_ids)
    if not is_push_success:
        perror_log("Failed to push local ip address to AWS database")
        sys.exit(0)

    tap_success = False
    # Update current batch count based on the loaded tap data
    current_batch_count = len(operation_taps["Records"])
    
    print_log("Starting Display")
    try:
        while True:
            # Display the relevant data on the screen
            draw_display(last_tags_and_ids)
            time.sleep(0.25)
            fifo_data = read_from_file(FILE_PATH_INFO.FIFO_PATH)
            if not fifo_data:
                continue
            fifo_data_split = fifo_data.split("::")
            program_name = fifo_data_split[0]
            if program_name == "operation_tap_listener.c":
                timestamp = fifo_data_split[1]
            else if program_name == "nfc_tap_listener.c":
                if not handle_nfc_tap(table, fifo_data, last_tags_and_ids):
                    perror_log(f"Error: NFC tap not registered \n FIFO Data: {fifo_data}")
                    tap_success = False
            else:
                perror_log(f"Error: invalid program name \n FIFO Data: {fifo_data}")
                
            with open(FILE_PATH_INFO.FIFO_PATH, "r") as fifo:
                data = fifo.read()
                if data:
                    print(data)
                    data = data.split("-program-")
                    formatted_time = get_current_time(format_seconds=False)
                    formatted_time_sec = get_current_time(format_seconds=True)
                    if data[0] == "read_ultralight.c":
                        if data[1][:-1] == "Failed":
                            tap_success = False
                        else:
                            tagId = data[1][:-1].lower()
                            request_data = {
                                'table_name': 'tbl6vse0gHkuPxBaT',
                                'filter_id': 'fldRHuoXAQr4BF83j',
                                'filter_value': tagId,
                                'field_mappings': [
                                    ("fldRi8wjAdfBkDhH8", "record_id"),
                                    ("fldSrxknmVrsETFPx", "order_id")
                                ]
                            }
                            success, partition_key = push_item_db(
                                dynamodb, "GetRecord", request_data)
                            if success:
                                success, db_data = pull_item_db(
                                    dynamodb, partition_key)
                                if success:
                                    order_dict = json.loads(db_data['Data'])[
                                        'Records'][0]
                                    print(order_dict)
                            field_ids = [
                                ("fldSrxknmVrsETFPx", "order_id"), ("fldRi8wjAdfBkDhH8", "record_id")]
                            order_dict = get_record(
                                "appZUSMwDABUaufib", "tbl6vse0gHkuPxBaT", field_ids, "fldRHuoXAQr4BF83j", tagId)
                            # When an employee tag is registered, the session unit counting is reset
                            if order_dict:  # Order tag is registered
                                if tagId != last_tags_and_ids["last_order_tag"]:
                                    if last_tags_and_ids["last_employee_record_id"] == "None":
                                        tap_success = False
                                    else:
                                        last_tags_and_ids["last_order_record_id"] = order_dict["record_id"]
                                        request_data = {
                                            "machine_record_id": [last_tags_and_ids["machine_record_id"]],
                                            "order_tag_record_id": [last_tags_and_ids["last_order_record_id"]],
                                            "employee_tag_record_id": [last_tags_and_ids["last_employee_record_id"]]
                                        }
                                        if push_item_db(dynamodb, "OrderNFC", request_data):
                                            print_log("NFC Order Tapped")
                                            last_tags_and_ids["last_order_tag"] = tagId
                                            last_tags_and_ids["last_order_tap"] = formatted_time
                                            last_tags_and_ids["units_order"] = 0
                                            last_tags_and_ids["order_id"] = "None" if order_dict[
                                                "order_id"] == "None" else order_dict["order_id"][0]
                                        else:
                                            tap_success = False
                            else:  # Unregistered tag treated as employee tag or employee tag is registered
                                if tagId != last_tags_and_ids["last_employee_tag"]:
                                    last_employee_record_id_temp = last_tags_and_ids[
                                        "last_employee_record_id"]
                                    employee_name_temp = last_tags_and_ids["employee_name"]
                                    # TODO: NEED TO IMPLEMENT GetRecord API CALL THROUGH EC2
                                    field_ids = [
                                        ("fldOYvm4LsaM9pJNw", "employee_name"), ("fld49C1CkqgW9hA3p", "record_id")]
                                    employee_dict = get_record("appZUSMwDABUaufib", "tblbRYLt6rr4nTbP6", field_ids,
                                                               "fldyYKc2g0dBdolKQ", tagId)
                                    if employee_dict:
                                        last_tags_and_ids["employee_name"] = employee_dict["employee_name"][0]
                                        last_tags_and_ids["last_employee_record_id"] = employee_dict["record_id"]
                                    else:
                                        last_tags_and_ids["employee_name"] = tagId
                                        # TODO: NEED TO IMPLEMENT CreateRecord API CALL THROUGH EC2
                                        field_data = {
                                            "fldyYKc2g0dBdolKQ": tagId}
                                        tag_record = create_record("appZUSMwDABUaufib", "tblbRYLt6rr4nTbP6",
                                                                   field_data)
                                        last_tags_and_ids["last_employee_record_id"] = tag_record["records"][0]["fields"]["Record ID"]
                                    request_data = {
                                        "machine_record_id": [last_tags_and_ids["machine_record_id"]],
                                        "employee_tag_record_id": [last_tags_and_ids["last_employee_record_id"]]
                                    }
                                    if push_item_db(dynamodb, "EmployeeNFC", request_data):
                                        print_log("NFC Employee Tapped")
                                        last_tags_and_ids["last_employee_tag"] = tagId
                                        last_tags_and_ids["last_employee_tap"] = formatted_time
                                        last_tags_and_ids["units_order"] = 0
                                        last_tags_and_ids["units_employee"] = 0
                                    else:
                                        last_tags_and_ids["last_employee_record_id"] = last_employee_record_id_temp
                                        last_tags_and_ids["employee_name"] = employee_name_temp
                                        tap_success = False
                    else:  # Button tap increases unit count
                        if last_tags_and_ids["last_employee_tag"] != "None" and last_tags_and_ids["last_order_tag"] != "None":
                            print_log("Button Pressed")
                            request_data = {
                                "machine_record_id": last_tags_and_ids["machine_record_id"],
                                "employee_tag_record_id": last_tags_and_ids["last_employee_record_id"],
                                "order_tag_record_id": last_tags_and_ids["last_order_record_id"],
                                "timestamp": formatted_time_sec
                            }
                            operation_taps["Records"].append(request_data)
                            current_count += 1
                            # TODO: Create CSV file and send it to a) Google Drive (link notifications with Slack)
                            if current_count >= BATCH_SIZE:  # May have to partition into multiple batches of 10
                                if push_item_db(dynamodb, "TapEvent", operation_taps):
                                    current_count = 0
                                    operation_taps = {"Records": []}
                                else:
                                    tap_success = False
                            last_tags_and_ids["units_order"] += 1
                            last_tags_and_ids["units_employee"] += 1
                        else:
                            tap_success = False
                        save_batch_to_file(operation_taps)
                    save_last_tags_and_ids_to_file(last_tags_and_ids)
                    temp_color = (0, 170, 0)
                    if not tap_success:
                        temp_color = (0, 0, 255)
                        tap_success = True
                    draw_display(last_tags_and_ids, bg_color=temp_color)
            time.sleep(0.25)
    except KeyboardInterrupt:
        print_log("Program Interrupted")


if __name__ == "__main__":
    main()
