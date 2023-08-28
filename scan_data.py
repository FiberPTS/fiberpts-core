#!/usr/bin/python3.9
import boto3
import json
import configparser
import time
import os

config = configparser.ConfigParser()
config.read(os.path.expanduser('~/.aws/credentials.txt'))

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

for item in response['Items']:
    print(item)
    print()
    print()