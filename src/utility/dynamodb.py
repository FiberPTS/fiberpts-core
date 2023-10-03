#!/usr/bin/python3.9
import boto3
import json
import configparser
import time
import os
import argparse

def delete_all_items(table):
    """
    Deletes all items from the given DynamoDB table.

    Args:
        table: boto3 DynamoDB Table object

    Returns:
        None
    """
    try:
        # Scan the table to get all items
        scanned_items = table.scan()['Items']

        # Iterate over each item
        for item in scanned_items:
            key = {}
            # Assuming 'partitionKey' is your primary key
            if 'partitionKey' in item:
                key['partitionKey'] = item['partitionKey']

            # Only delete if key exists
            if key:
                table.delete_item(Key=key)

        print("All items deleted successfully.")
    except Exception as e:
        print(f"An error occurred while deleting items: {e}")


def scan_table(table):
    """
    Scans and prints all items from the given DynamoDB table.

    Args:
        table: boto3 DynamoDB Table object

    Returns:
        None
    """
    response = table.scan()
    for item in response['Items']:
        print(item)
        print()
        print()


if __name__ == "__main__":
    # Command-line argument handling
    parser = argparse.ArgumentParser(description='Delete or scan DynamoDB table.')
    parser.add_argument('--delete', action='store_true', help='Delete all items in the table')
    parser.add_argument('--scan', action='store_true', help='Scan the table')
    args = parser.parse_args()

    # Read AWS credentials from the specified file
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.aws/credentials.txt'))

    aws_access_key_id = config.get('Credentials', 'aws_access_key_id')
    aws_secret_access_key = config.get('Credentials', 'aws_secret_access_key')

    # Initialize DynamoDB resource with the provided credentials
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name='us-east-1'
    )

    # Initialize DynamoDB table
    table = dynamodb.Table('API_Requests')

    # Execute corresponding function based on command-line arguments
    if args.delete:
        delete_all_items(table)
    elif args.scan:
        scan_table(table)
    else:
        print("No action specified. Use --delete to delete all items in the table or --scan to scan the table.")