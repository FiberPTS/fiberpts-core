import json
import time
from log_utils import *
from utils import *


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
