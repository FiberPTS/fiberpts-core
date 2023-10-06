from utility.utils import *
from utility.file_utils import *
from utility.log_utils import *
from utility.dynamodb_utils import *
import boto3
import json
import configparser


def initialize_dynamodb(table_name):
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
    table = dynamodb.Table(table_name)
    return table


class DynamoDBTapHandler:

    def __init__(self, table_name, file_path_info, batch_size):
        self.table = initialize_dynamodb(table_name)
        self.file_path_info = file_path_info
        self.batch_size = batch_size

    def pull_last_tags_and_ids(self):
        """
        Update the `last_tags_and_ids` dictionary with data from the database.

        Args:
            table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.

        Returns:
            tuple: A tuple containing two elements:
                - bool: True if the data was successfully retrieved and updated, False otherwise.
                - dict: The updated `last_tags_and_ids` dictionary.
        """
        last_tags_and_ids = load_json_from_file(self.file_path_info.LAST_TAGS_AND_IDS)
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

            is_push_success, partition_key = push_item_db(self.table, "GetRecord", request_data)

            if is_push_success:
                is_pull_success, data = pull_item_db(self.table, partition_key)

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

    def push_local_ip_to_db(self, last_tags_and_ids):
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
        if push_item_db(self.table, "LocalIPAddress", request_data)[0]:
            print_log(f"Local IP Address pushed successfully: {local_ip}")
            return True
        else:
            return False

    def handle_operation_tap(self, last_tags_and_ids, operation_taps, current_batch_count, timestamp):
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
        # if last_tags_and_ids["last_employee_tag"] != "None" and last_tags_and_ids["last_order_tag"] != "None":
        #     print_log("Button Pressed")
        #     # TODO: Make sure timestamp is in correct format with seconds
        #     request_data = {
        #         "machine_record_id": last_tags_and_ids["machine_record_id"],
        #         "employee_tag_record_id": last_tags_and_ids["last_employee_record_id"],
        #         "order_tag_record_id": last_tags_and_ids["last_order_record_id"],
        #         "timestamp": timestamp
        #     }
        #     operation_taps["Records"].append(request_data)
        #     current_batch_count += 1
        #     if current_batch_count >= self.batch_size:
        #         if not push_item_db(self.table, "OperationTapEvent", operation_taps):
        #             return False, operation_taps, current_batch_count
        #         current_batch_count = 0
        #         operation_taps = {"Records": []}
        #
        #     last_tags_and_ids.update({
        #         "units_order": last_tags_and_ids["units_order"] + 1,
        #         "units_employee": last_tags_and_ids["units_employee"] + 1
        #     })
        # else:
        #     return False, operation_taps, current_batch_count
        #
        # return True, operation_taps, current_batch_count
        tap_record = {
            "Machine ID": get_machine_id(),
            "UoM": 1,
            "Timestamp": timestamp
        }
        operation_taps["Records"].append(tap_record)


    def handle_employee_tap(self, last_tags_and_ids, tag_uid, timestamp):
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

        pull_success, employee_record = get_record(self.table, request_data)

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
            employee_record = create_record(self.table, request_data)
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

        push_success = push_item_db(self.table, "EmployeeNFC", request_data)

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

    def handle_nfc_tap(self, last_tags_and_ids, tag_uid, timestamp):
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

        pull_success, order_record = get_record(self.table, request_data)

        if not order_record:
            return self.handle_employee_tap(self.table, last_tags_and_ids, tag_uid, timestamp)

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

        if not push_item_db(self.table, "OrderNFC", request_data):
            return False

        return True
