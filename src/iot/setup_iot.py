# Import necessary modules
from fabric import Connection
from collections import namedtuple
from dotenv import load_dotenv
import os
import argparse
import requests
import json
import sys
import time

# Create an argument parser
parser = argparse.ArgumentParser(
    description='Run setup on a Linux device via SSH.')
parser.add_argument(
    '--ip', help='The IP address of the device.', required=True)
parser.add_argument('--usr', help='The username for SSH.', required=True)
parser.add_argument('--pw', help='The password for SSH.', required=True)
parser.add_argument(
    '--driver', choices=['wn725n', 'ac600'], help='The driver to install.', required=True)
parser.add_argument(
    '--wifi_name', help='The WiFi name to connect to.', required=True)
parser.add_argument('--wifi_pw', help='The WiFi password.', required=True)

# Parse the provided command-line arguments
args = parser.parse_args()

# Extract values from the parsed arguments
ip = args.ip
username = args.usr
password = args.pw
driver = args.driver
wifi_name = args.wifi_name
wifi_pw = args.wifi_pw

# AWS and Airtable credentials
ApiKeys = namedtuple(
    'ApiKeys',
    ['AWS_ACCESS', 'AWS_SECRET', 'AIRTABLE']
)

load_dotenv()

API_KEYS = ApiKeys(
    AWS_ACCESS=os.getenv('AWS_ACCESS_KEY'),
    AWS_SECRET=os.getenv('AWS_SECRET_KEY'),
    AIRTABLE_API_KEY=os.getenv('AIRTABLE_API_KEY')
)

for envar in API_KEYS.keys():
    if not API_KEYS.envar:
        raise ValueError(f"'{envar}' is not set.")

# Establish an SSH connection
c = Connection(host=ip, user=username, connect_kwargs={"password": password})
c.config.sudo.password = password

# Check if git is installed and update the package list
c.sudo('apt-get update -y')
result = c.run('command -v git', warn=True)
# If git is not installed, install it
if result.failed:
    c.sudo('apt-get install -y git')

# Check if the directory /home/username/NFC_Tracking exists
# TODO: Change directory naming from "NFC_Tracking" to "FiberPTS"
result = c.run(f"ls /home/{username}/NFC_Tracking", warn=True)

# If it doesn't exist, clone the repository
# TODO: Use var to store repo url and repo name
# TODO: Update repository url
if result.failed:
    c.run(
        f"git clone https://github.com/NxFerrara/NFC_Tracking.git /home/{username}/NFC_Tracking")

# Run the configuration script with the specified driver
c.sudo(f"sh /home/{username}/NFC_Tracking/configure.sh {driver}")

# Create a file with AWS credentials
credential_content = f"""
[Credentials]
aws_access_key_id = {API_KEYS.AWS_ACCESS}
aws_secret_access_key = {API_KEYS.AWS_SECRET}
"""
credential_file_path = f"/home/{username}/.aws/credentials.txt"
c.run(f"mkdir -p /home/{username}/.aws/")
c.run(f"echo '{credential_content}' > {credential_file_path}")
c.run(f"chmod 600 {credential_file_path}")

# Create a file with Airtable credentials
airtable_credential_content = f"""
[Credentials]
airtable_api_key = {API_KEYS.AIRTABLE}
"""
airtable_credential_file_path = f"/home/{username}/.airtable/credentials.txt"
c.run(f"mkdir -p /home/{username}/.airtable/")
c.run(f"echo '{airtable_credential_content}' > {airtable_credential_file_path}")
c.run(f"chmod 600 {airtable_credential_file_path}")

# Notify the user that the board setup is complete and initiate a reboot
print("Board setup complete! Reboot Started")

# Shutdown the system
try:
    c.sudo('shutdown now')
except Exception as e:
    print("The system is shutting down as expected.")

# Wait for the Raspberry Pi to reboot
print("Waiting for the Raspberry Pi to reboot...")
time.sleep(30)  # Adjust this value as needed

# Try to reconnect to the board
while True:
    try:
        c = Connection(host=ip, user=username,
                       connect_kwargs={"password": password})
        time.sleep(10)
        break
    except Exception as e:
        print("Failed to reconnect, trying again in 10 seconds...")
        time.sleep(10)

# Once reconnected, run the nmcli command to connect to the specified WiFi
print("Connected! Running nmcli command...")
c.sudo(f"nmcli device wifi connect {wifi_name} password {wifi_pw}")
print("Done!")
