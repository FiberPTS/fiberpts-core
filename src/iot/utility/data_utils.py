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


def push_item_db(table, request_type, request_data):
    """
    Pushes an item to a DynamoDB table.

    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
        request_type: The type of request.
        request_data: The data for the request.

    Returns:
        tuple: A tuple containing a boolean indicating success and the partition key.
    """
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
        if status == 200:
            return True, partition_key
    perror_log(f"An error occurred while pushing the item: \n Data: {request_data} \n MetaData: {meta_data}")
    return False, None


def pull_item_db(table, partition_key, max_attempts=5):
    """
    Pulls an item from a DynamoDB table based on the partition key.

    Args:
        table (boto3.DynamoDB.Table): The boto3 DynamoDB table resource.
        partition_key: The partition key for the item.
        max_attempts: The maximum number of attempts to retrieve the item.

    Returns:
        tuple: A tuple containing a boolean indicating success and the item data or an error message.
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


def get_record(table, request_data):
    """
    Fetch a record from the AWS DynamoDB based on the provided request data.

    Args:
        table: The boto3 DynamoDB table resource.
        request_data (dict): The data required to make the request.

    Returns:
        tuple: (bool, dict or None)
            bool: True if data was successfully retrieved, False otherwise.
            dict: The record data retrieved from the database, or None if retrieval was unsuccessful.
    """
    success, partition_key = push_item_db(table, "GetRecord", request_data)

    if success:
        success, db_data = pull_item_db(table, partition_key)
        if success and 'Data' in db_data:
            json_data = json.loads(db_data['Data'])['Records'][0]
            return True, json_data

    return False, None


def create_record(table, request_data):
    """
    Create a record to be pushed to the Airtable DB based on the provided request data.

    Args:
        table: The boto3 DynamoDB table resource.
        request_data (dict): The data required to make the request.

    Returns:
        tuple: (bool, dict or None)
            bool: True if data was successfully retrieved, False otherwise.
            dict: The record data retrieved from the database, or None if retrieval was unsuccessful.
    """
    success, partition_key = push_item_db(table, "CreateRecord", request_data)

    # TODO: Return record id of the created record.
    if success:
        success, db_data = pull_item_db(table, partition_key)
        if success and 'Data' in db_data:
            json_data = json.loads(db_data['Data'])['Records'][0]
            return True, json_data

    return False, None
