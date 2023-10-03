# Import necessary modules
from fabric import Connection
from dotenv import load_dotenv
from collections import namedtuple
import argparse
import requests
import json
import sys
import os

# Create an argument parser
parser = argparse.ArgumentParser(
    description='Run a command on a Linux machine via SSH.')
parser.add_argument('--command', help='The command to run.', required=True)
parser.add_argument('--ip', help='The IP address of the machine.')
parser.add_argument('--all', action='store_true',
                    help='Run the command on all machines.')
parser.add_argument('--usr', default='potato', help='The username for SSH.')
parser.add_argument('--pw', default='carmine1981',
                    help='The password for SSH.')

# Parse the provided command-line arguments
args = parser.parse_args()

# Extract values from the parsed arguments
command = args.command
ip = args.ip
all_machines = args.all
username = args.usr
password = args.pw

# Airtable constants
AirtableInfo = namedtuple(
    'AirtableInfo',
    ['BASE_ID', 'TABLE_NAME', 'API_KEY']
)

load_dotenv()

AIRTABLE_INFO = AirtableInfo(
    BASE_ID='appZUSMwDABUaufib',
    TABLE_NAME='tblFOfDowcZNlPRDL',
    KEY=os.getenv('AIRTABLE_API_KEY')
)

if not AIRTABLE_INFO.KEY:
    raise ValueError("'AIRTABLE_INFO' is not set.")

# Initialize variables
ips = []
offset = None

# Fetch IP addresses from Airtable if the --all flag is set
while all_machines:
    headers = {'Authorization': 'Bearer ' + AIRTABLE_INFO.KEY}
    params = {'pageSize': 100}
    if offset:
        params['offset'] = offset
    response = requests.get(
        f'https://api.airtable.com/v0/{AIRTABLE_INFO.BASE_ID}/{AIRTABLE_INFO.TABLE_NAME}?fields%5B%5D=fldjOFa17u7mRjN0a', 
        headers=headers, 
        params=params
    )
    data = response.json()
    # fetch the value of the first field
    ips.extend([list(record['fields'].values())[0]
               for record in data['records']])
    offset = data.get('offset')
    if not offset:
        break

# If the --ip argument is used, override the IPs list with that single IP
if ip:
    ips = [ip]
# If neither --ip nor --all are used, print an error message and exit
elif not all_machines:
    print("Please provide either --ip or --all.")
    sys.exit(1)

# SSH into each IP address and run the specified command
# TODO: Change directory name from 'NFC_Tracking' to 'FiberPTS'
for ip in ips:
    c = Connection(host=ip, user=username,
                   connect_kwargs={"password": password})
    c.config.sudo.password = password
    # Check if the directory /home/username/NFC_Tracking exists
    result = c.run(f"ls /home/{username}/NFC_Tracking", warn=True)
    if result.failed:
        print(f"Device {ip} needs to be setup")
    else:
        # Execute the command in the /home/username/NFC_Tracking directory
        c.sudo(f"sh -c 'cd /home/{username}/NFC_Tracking; {command}'")
