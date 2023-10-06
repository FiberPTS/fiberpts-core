import boto3
import configparser
import json
import time
from utility.utils import *
from utility.file_utils import *
from utility.log_utils import *
from utility.dynamodb_utils import *


def initialize_dynamodb(table_name):
    """
    Initializes a DynamoDB resource using AWS credentials and returns
    a table object.

    Args:
      table_name (str): The name of the DynamoDB table to be initialized.

    Returns:
      A DynamoDB table object.
    """
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


class DynamoDB:

    def __init__(self, table_name, file_path_info, batch_size):
        self.table = initialize_dynamodb(table_name)
        self.file_path_info = file_path_info
        self.batch_size = batch_size

    def push_item_db(self, table, request_type, request_data):
        """
        Pushes an item to a DynamoDB table.

        Args:
            table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
            request_type: The type of request.
            request_data: The data for the request.

        Returns:
            tuple: A tuple containing:
              - bool: True to indicate successful push, False otherwise.
              - str: DynamoDB's partition key.
        """
        HTTP_OK = 200

        partition_key = f'{get_machine_id()}-{request_type}-{get_current_time()}'
        response = table.put_item(
            Item={
                'partitionKey': partition_key,
                'Request_Type': request_type,
                'Data': json.dumps(request_data),
                'Status': 'Pending',
            }
        )

        meta_data = response.get('ResponseMetadata', 'None')
        if meta_data != 'None':
            status = meta_data.get('HTTPStatusCode', 'None')
            if status == HTTP_OK:
                return True, partition_key

        perror_log(
            f"An error occurred while pushing the item: \n Data: {request_data} \n MetaData: {meta_data}")
        return False, None

    def pull_item_db(self, table, partition_key, max_attempts=5):
        """
        Pulls an item from a DynamoDB table based on the partition key.

        Args:
            table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
            partition_key (str): The partition key for the item.
            max_attempts (int): The maximum number of attempts to retrieve the item.

        Returns:
            tuple: A tuple containing:
              - bool: True if successful pull, False otherwise.
              - str: Item data or an error message.
        """
        attempts = 1
        while attempts <= max_attempts:
            try:
                # Retrieve the item from the DynamoDB table
                response = table.get_item(
                    Key={
                        'partitionKey': partition_key
                    }
                )

                # Extract the item from the response
                item = response.get('Item', {})

                # Check if the item exists and has the status "Complete"
                if item and item.get('Status') == 'Complete':
                    key = {
                        'partitionKey': partition_key
                    }
                    table.delete_item(Key=key)
                    return True, item
                
                attempts += 1
                time.sleep(0.1)
            except Exception as e:
                perror_log(f"An error occurred while pulling the item: {e}")
                return False, f"An error occurred: {e}"

        return False, "Item not found or not complete"

    def get_record(self, table, request_data):
        """
        Fetch a record from the AWS DynamoDB based on the provided request data.

        Args:
            table: The boto3 DynamoDB table resource.
            request_data (dict): The data required to make the request.

        Returns:
            tuple: (bool, dict or None)
              - bool: True if data was successfully retrieved, False otherwise.
              - dict: The record data retrieved from the database, or None if retrieval was unsuccessful.
        """
        success, partition_key = self.push_item_db(table, "GetRecord", request_data)

        if success:
            success, db_data = self.pull_item_db(table, partition_key)
            if success and 'Data' in db_data:
                json_data = json.loads(db_data['Data'])['Records'][0]
                return True, json_data

        return False, None

    def create_record(self, table, request_data):
        """
        Create a record to be pushed to the Airtable DB based on the provided request data.

        Args:
            table: The boto3 DynamoDB table resource.
            request_data (dict): The data required to make the request.

        Returns:
            tuple: (bool, dict or None)
              - bool: True if data was successfully retrieved, False otherwise.
              - dict: The record data retrieved from the database, or None if retrieval was unsuccessful.
        """
        success, partition_key = self.push_item_db(
            table, "CreateRecord", request_data)

        # TODO: Return record id of the created record.
        if success:
            success, db_data = self.pull_item_db(table, partition_key)
            if success and 'Data' in db_data:
                json_data = json.loads(db_data['Data'])['Records'][0]
                return True, json_data

        return False, None


class DynamoDBTapHandler(DynamoDB):

    def pull_latest_tags_and_ids(self):
        """
        Updates the `latest_tags_and_ids` dictionary with data from the database.

        Args:
            table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.

        Returns:
            tuple: A tuple containing:
              - bool: True if the data was successfully retrieved and updated, False otherwise.
              - dict: The updated `last_tags_and_ids` dictionary.
        """
        last_tags_and_ids = load_json_from_file(
            self.file_path_info.LAST_TAGS_AND_IDS)
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

            is_push_success, partition_key = self.push_item_db(
                self.table, "GetRecord", request_data)

            if is_push_success:
                is_pull_success, data = self.pull_item_db(
                    self.table, partition_key)

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
        if self.push_item_db(self.table, "LocalIPAddress", request_data)[0]:
            print_log(f"Local IP Address pushed successfully: {local_ip}")
            return True
        return False

    def handle_operation_tap(self, tags_and_ids, operation_taps, current_batch_count, timestamp):
        """
        Handle a button tap event by updating the `operation_taps` dictionary with
        relevant data and checking if the batch size has been reached.

        Args:
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
        if tags_and_ids["last_employee_tag"] != "None" and tags_and_ids["last_order_tag"] != "None":
            print_log("Button Pressed")
            request_data = {
                "machine_record_id": tags_and_ids["machine_record_id"],
                "employee_tag_record_id": tags_and_ids["last_employee_record_id"],
                "order_tag_record_id": tags_and_ids["last_order_record_id"],
                "timestamp": timestamp
            }

            operation_taps["Records"].append(request_data)
            current_batch_count += 1

            if current_batch_count >= self.batch_size:
                if not self.push_item_db(self.table, "OperationTapEvent", operation_taps):
                    return False, operation_taps, current_batch_count
                current_batch_count = 0
                operation_taps = {"Records": []}

            tags_and_ids.update({
                "units_order": tags_and_ids["units_order"] + 1,
                "units_employee": tags_and_ids["units_employee"] + 1
            })
        else:
            return False, operation_taps, current_batch_count

        return True, operation_taps, current_batch_count

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

        pull_success, employee_record = self.get_record(
            self.table, request_data)

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
            employee_record = self.create_record(self.table, request_data)
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

        push_success = self.push_item_db(
            self.table, "EmployeeNFC", request_data)

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

        pull_success, order_record = self.get_record(self.table, request_data)

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

        if not self.push_item_db(self.table, "OrderNFC", request_data):
            return False

        return True
