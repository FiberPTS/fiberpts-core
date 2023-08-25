#!/usr/bin/python3.9
import boto3
import json
import configparser

config = configparser.ConfigParser()
config.read('/home/potato/NFC_Tracking/.aws/credentials.txt')

aws_access_key_id = config.get('Credentials', 'aws_access_key_id')
aws_secret_access_key = config.get('Credentials', 'aws_secret_access_key')

client = boto3.client(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name='us-east-1'
)

table = dynamodb.Table('API_Requests')

# Data should be a JSON-serialized string
data = json.dumps({"key1": "value1", "key2": "value2"})

# Insert item
response = table.put_item(
   Item={
        'partitionKey': 'SomePartitionKeyValue',
        'Request_Type': 'TapEvent',
        'Data': data,
        'Status': 'Pending',
        'Timestamp': '2023-08-25T14:00:00Z'
    }
)

print("PutItem succeeded:", response)