#!/usr/local/bin/python3.10

# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary

# Standard library imports
# import time
# import sys
# import os
# import configparser

# Third-party imports
# from dotenv import load_dotenv
from collections import namedtuple
# import boto3

# Local project libraries
# from utility.utils import *
from utility.display_utils import *
from utility.file_utils import *
from utility.log_utils import *
from utility.signal_utils import *
from utility.csv_utilities import *
# from dynamodb_controller import *


# File Paths
FilePathConstants = namedtuple("FilePathConstants", ["DATA_FOLDER", "OPERATION_TAPS", "LAST_TAGS_AND_IDS", "FIFO_PATH"])
FILE_PATH_INFO = FilePathConstants(
    DATA_FOLDER="/var/lib/tap_event_handler",
    OPERATION_TAPS="/var/lib/tap_event_handler/operation_taps.json",
    LAST_TAGS_AND_IDS="/var/lib/tap_event_handler/last_tags_and_ids.json",
    FIFO_PATH="/tmp/tap_event_handler"
)

# # Load environment variables
# load_dotenv()
#
# # Constants for Airtable configurations
# AirtableConstants = namedtuple("AirtableConstants", ["API_KEY"])
# AIRTABLE_CONST = AirtableConstants(API_KEY=os.getenv('AIRTABLE_API_KEY'))
#
# # Check for mandatory environment variables
# if not AIRTABLE_CONST.API_KEY:
#     raise ValueError("'AIRTABLE_API_KEY' is not set.")

# Constants
BATCH_SIZE = 10
# TABLE_NAME = "API_Requests"
MACHINE_ID = get_machine_id()


def main():
    # Initialize signal handlers
    initialize_signal_handlers(["SIGTERM"])

    # # Read the Airtable API Key
    # airtable_config = configparser.ConfigParser()
    # airtable_config.read("/home/potato/.airtable/credentials.txt")

    # Print initialization logs
    print_log("Starting Screen.py")
    print_log("Pulling Previous Data")

    # db_handler = DynamoDBTapHandler(TABLE_NAME, FILE_PATH_INFO, BATCH_SIZE)

    # # Pull the last set of tags and IDs from the database
    # is_update_success, last_tags_and_ids = db_handler.pull_last_tags_and_ids()
    # if not is_update_success:
    #     perror_log("Failed to update last_tags_and_ids from AWS database")
    #     sys.exit(0)


    # # Push the latest local ip to the database
    # # TODO: Figure out if we can make local ip static instead of dynamic
    # is_push_success = db_handler.push_local_ip_to_db(last_tags_and_ids)
    # if not is_push_success:
    #     perror_log("Failed to push local ip address to AWS database")
    #     sys.exit(0)

    # Load batched button presses from a file
    operation_taps = load_json_from_file(FILE_PATH_INFO.OPERATION_TAPS, default_value={"Records": []})

    # # Update the current batch count based on the loaded tap data
    # current_batch_count = len(operation_taps["Records"])

    print_log("Starting Display")

    # Initialize the display manager
    display_manager = DisplayManager()

    try:
        while True:
            if ready_to_upload():
                if upload_report(operation_taps, FILE_PATH_INFO.DATA_FOLDER):
                    operation_taps["Records"] = []
                    print_log(program_name, "Successfully created and uploaded data report")

            time.sleep(0.25)
            tap_success = True

            # Display the relevant data on the screen
            # display_manager.draw_display(last_tags_and_ids)
            display_manager.draw_display(operation_taps)

            # Read data from the FIFO Pipe
            fifo_data = read_from_file(FILE_PATH_INFO.FIFO_PATH)
            if not fifo_data:
                continue

            fifo_data_split = fifo_data.split("::")
            program_name = fifo_data_split[0]

            # Handle operation taps
            if program_name == "operation_tap_listener.c":
                # TODO: Save operation taps to a CSV file and push CSV file to Google Drive at x:xxpm every day (daily)
                timestamp = fifo_data_split[1]
                # push_success, operation_taps, current_batch_count = db_handler.handle_operation_tap(
                #     last_tags_and_ids,
                #     operation_taps,
                #     current_batch_count,
                #     timestamp
                # )
                # if not push_success:
                #     perror_log(f"Error: Operation taps not registered \n FIFO Data: {fifo_data}")
                #     tap_success = False
                tap_record = {
                    "Machine ID": get_machine_id(),
                    "UoM": 1,
                    "Timestamp": timestamp
                }
                operation_taps["Records"].append(tap_record)
                save_json_to_file(FILE_PATH_INFO.OPERATION_TAPS, operation_taps)

            # Handle NFC taps
            elif program_name == "nfc_tap_listener.c":
                tag_uid = fifo_data_split[1].lower()
                timestamp = fifo_data_split[2]
                # if not db_handler.handle_nfc_tap(last_tags_and_ids, tag_uid, timestamp):
                #     perror_log(f"Error: NFC tap not registered \n FIFO Data: {fifo_data}")
                #     tap_success = False

            # Handle invalid program names
            else:
                perror_log(f"Error: invalid program name \n FIFO Data: {fifo_data}")

            # Save the last tags and IDs to a file
            # save_json_to_file(FILE_PATH_INFO.LAST_TAGS_AND_IDS, last_tags_and_ids)

            # Update the display with the background color indicating success or failure
            bg_color = (0, 170, 0) if tap_success else (0, 0, 255)
            # display_manager.draw_display(last_tags_and_ids, bg_color=bg_color)
            display_manager.draw_display(operation_taps, bg_color=bg_color)
    except KeyboardInterrupt:
        print_log("Program Interrupted")


if __name__ == "__main__":
    main()
