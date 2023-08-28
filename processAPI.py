#!/usr/bin/python3
import boto3
import json
import configparser
import time
import requests
import os


AIRTABLE_API_URL = "https://api.airtable.com/v0/appZUSMwDABUaufib/"
AIRTABLE_API_KEY = "patAQ8FpGw4j3oKk2.5f0606ba0571c34a403bdd282a25681187c1ac5f37050cca35a880e4def1a5ee"


def delete_records(table, records):
    for item in records:
        key = {
            'partitionKey': item['partitionKey']
            # Replace 'PrimaryKeyAttribute' with the actual primary key attribute name of your table
        }
        table.delete_item(Key=key)


def update_failed_requests(table, to_update, request_attempts):
    for req in to_update:
        key = {
            'partitionKey': req['partitionKey']
        }
        table.update_item(
            Key=key,
            UpdateExpression="set #s = :s, #r = :r",
            ExpressionAttributeNames={
                '#s': 'Status',
                '#r': 'Reason'
            },
            ExpressionAttributeValues={
                ':s': 'Failed',
                ':r': request_attempts[req['partitionKey']]['errors']
            }
        )


def handle_tap_request(req):
    try:
        url = AIRTABLE_API_URL + "tblVoD1DTyiOAMJ5q"
        # Extract the data from the request
        data_str = req.get('Data', '')
        data_json = json.loads(data_str)

        records = data_json.get('Records', [])

        # Prepare the payload for Airtable API
        airtable_records = []
        for record in records:
            airtable_record = {
                "fields": {
                    "fldVQGXQ9CVW6KJkJ": [record.get("machine_record_id")],
                    "fldGx0sQJknx4CDFR": [record.get("employee_tag_record_id")],
                    "fld6jiNTUPVRKdf5d": [record.get("order_tag_record_id")],
                    "fldGYKh5CAUcqesbt": record.get("timestamp"),
                }
            }
            airtable_records.append(airtable_record)

        payload = {
            "records": airtable_records  # Limit to 10 records per batch
        }

        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }

        # Make the POST request to Airtable API
        response = requests.post(url, headers=headers, json=payload)

        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
        return True, None
    except requests.exceptions.RequestException as e:
        return False, str(e)
    except requests.exceptions.HTTPError as e:
        return False, f"Failed to create records: {response.json().get('error', {}).get('message', 'Unknown error')}"
    except json.JSONDecodeError as e:
        return False, str(e)


def handle_order_request(req):
    response_create = None
    response_update = None

    try:
        # For creating a record
        url_create = AIRTABLE_API_URL + "tblAUlYXhh2nTQTnT"

        # For updating a record
        url_update = AIRTABLE_API_URL + "tblFOfDowcZNlPRDL"

        data_str = req.get('Data', '')
        data_json = json.loads(data_str)

        # Prepare payload for Airtable API to create a new record
        airtable_create_payload = {
            "fields": {
                "fldoBxDoBfeizCwmT": data_json.get("machine_record_id"),
                "fldNHVn5USJIgTPB6": data_json.get("employee_tag_record_id"),
                "fldkG7dswfsYUx8ff": data_json.get("order_tag_record_id"),
            }
        }

        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }

        response_create = requests.post(url_create, headers=headers, json=airtable_create_payload)
        response_create.raise_for_status()

        # Prepare payload for Airtable API to update an existing record
        airtable_update_payload = {
            "fields": {
                "fldmO1onxH7BdHiQW": data_json.get("order_tag_record_id")
            }
        }

        # Assuming machine_record_id is the record id for the record to be updated
        url_update = f"{url_update}/{data_json.get('machine_record_id')}"

        response_update = requests.patch(url_update, headers=headers, json=airtable_update_payload)
        response_update.raise_for_status()

        return True, None

    except requests.HTTPError as e:
        if response_update:
            return False, f"Failed to update record: {response_update.json()}"
        else:
            return False, f"Failed to create record: {response_create.json()}"
    except Exception as e:
        return False, str(e)


def handle_employee_request(req):
    response_create = None

    try:
        # For creating a record
        url_create = AIRTABLE_API_URL + "tbloOK7gmmDK94hfc"

        # For updating a record
        url_update = AIRTABLE_API_URL + "tblFOfDowcZNlPRDL"
        reasons = req.get('Reason','')
        print(reasons)
        if reasons[0] != '2':
            data_str = req.get('Data', '')
            data_json = json.loads(data_str)

            # Prepare payload for Airtable API to create a new record
            airtable_create_payload = {
                "fields": {
                    "fldX6JBtp55h7kXeU": data_json.get("machine_record_id"),
                    "fld9mWGyROaCXDVqP": data_json.get("employee_tag_record_id"),
                }
            }

            headers = {
                "Authorization": f"Bearer {AIRTABLE_API_KEY}",
                "Content-Type": "application/json"
            }

            response_create = requests.post(url_create, headers=headers, json=airtable_create_payload)
            print("Created JSON:",response_create.json())
            response_create.raise_for_status()

        # Prepare payload for Airtable API to update an existing record
        airtable_update_payload = {
            "fields": {
                "fldc2HfWeQ6X58jiW": data_json.get("employee_tag_record_id"),
            }
        }

        # Assuming machine_record_id is the record id for the record to be updated
        url_update = f"{url_update}/{data_json.get('machine_record_id')}"

        response_update = requests.patch(url_update, headers=headers, json=airtable_update_payload)
        print("Update JSON:",response_update.json())
        response_update.raise_for_status()

        return True, None

    except requests.HTTPError as e:
        if response_create:
            return False, f"1-Failed to create record: {response_create.json()}"
        return False, f"2-Failed to update record: {response_update.json()}"
    except Exception as e:
        return False, str(e)


def handle_request(req):
    # Implement your logic for handling different 'Request_Type' here
    request_type = req.get('Request_Type', '')
    if request_type == 'TapEvent':
        # Handle TapEvent
        return handle_tap_request(req)
    elif request_type == 'EmployeeNFC':
        # Handle EmployeeNFC
        return handle_employee_request(req)
    elif request_type == 'OrderNFC':
        # Handle OrderNFC
        return handle_order_request(req)
    else:
        return False, f"Unknown request type: {request_type}"


def main():
    # Reading Airtable API Key
    airtable_config = configparser.ConfigParser()
    airtable_config.read(os.path.expanduser('~/.airtable/credentials.txt'))
    global AIRTABLE_API_KEY  # Making sure to use the global variable
    AIRTABLE_API_KEY = airtable_config.get('Credentials', 'airtable_api_key')

    aws_config = configparser.ConfigParser()
    aws_config.read(os.path.expanduser('~/.aws/credentials.txt'))
    aws_access_key_id = aws_config.get('Credentials', 'aws_access_key_id')
    aws_secret_access_key = aws_config.get('Credentials', 'aws_secret_access_key')

    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name='us-east-1'
    )

    table = dynamodb.Table('API_Requests')
    last_time = time.time()
    request_count = 0
    pending_requests = []
    handle_max = 1  # Max number of times a request should be attempted
    request_attempts = {}  # Dictionary to keep track of the number of attempts and error messages for each request
    empty_runs = 0

    while True:
        current_time = time.time()
        if current_time - last_time >= 1:
            last_time = current_time
            request_count = 0

        if not pending_requests:
            response = table.scan()
            pending_requests = [item for item in response['Items'] if item['Status'] == 'Pending']

        to_delete = []
        to_update = []

        for req in pending_requests:
            request_type = req.get('Request_Type')

            # If the request is of type OrderNFC or EmployeeNFC, check if there is enough room for 2 API calls
            if request_type in ['OrderNFC', 'EmployeeNFC']:
                expected_increment = 2
            else:
                expected_increment = 1

            # Check if adding this request would exceed the rate limit
            if request_count + expected_increment > 3:
                continue

            key = req['partitionKey']
            success, error_message = handle_request(req)

            if key not in request_attempts:
                request_attempts[key] = {'count': 0, 'errors': []}

            if request_attempts[key]['count'] >= handle_max:
                to_update.append(req)
                continue

            if success:
                to_delete.append(req)
                request_count += expected_increment  # Increment by the expected amount
            else:
                request_attempts[key]['count'] += 1
                request_attempts[key]['errors'].append(error_message)

        delete_records(table, to_delete)

        update_failed_requests(table, to_update, request_attempts)

        for req in to_delete + to_update:
            key = req['partitionKey']
            del request_attempts[key]
            pending_requests.remove(req)

        if len(to_delete) > 0:
            print(f"Requests Processed: {to_delete}")
            empty_runs = 0
        else:
            print("No Requests Processed")
            time.sleep(1)
            empty_runs += 1
        if empty_runs > 2:
            pass
            # DO STUFF DURING DOWNTOWN


if __name__ == "__main__":
    main()