#!/usr/bin/python3.9
import boto3
import json
import configparser
import time

def delete_records(table, records):
    for item in records:
        key = {
            'partitionKey': item['partitionKey']  # Replace 'PrimaryKeyAttribute' with the actual primary key attribute name of your table
        }
        table.delete_item(Key=key)

def main():
    config = configparser.ConfigParser()
    config.read('/home/ec2-user/.aws/credentials.txt')

    aws_access_key_id = config.get('Credentials', 'aws_access_key_id')
    aws_secret_access_key = config.get('Credentials', 'aws_secret_access_key')

    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name='us-east-1'
    )

    table = dynamodb.Table('API_Requests')

    response = table.scan()
    pending_requests = [item for item in response['Items'] if item['Status'] == 'Pending']

    for req in pending_requests:
        print(req)

    # Delete the pending requests
    delete_records(table, pending_requests)
    response = table.scan()
    pending_requests = [item for item in response['Items'] if item['Status'] == 'Pending']

    for req in pending_requests:
        print(req)

if __name__ == "__main__":
    main()
