#!/usr/bin/python3.9
import boto3
import json
import configparser
import time
import os
import argparse


def delete_all_items(table):
    try:
        scanned_items = table.scan()['Items']

        for item in scanned_items:
            key = {}
            if 'partitionKey' in item:  # Assuming 'partitionKey' is your primary key
                key['partitionKey'] = item['partitionKey']

            if key:  # Only delete if key exists
                table.delete_item(Key=key)

        print("All items deleted successfully.")
    except Exception as e:
        print(f"An error occurred while deleting items: {e}")


def scan_table(table):
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

    # Read AWS credentials
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.aws/credentials.txt'))

    aws_access_key_id = config.get('Credentials', 'aws_access_key_id')
    aws_secret_access_key = config.get('Credentials', 'aws_secret_access_key')

    # Initialize DynamoDB resource
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
