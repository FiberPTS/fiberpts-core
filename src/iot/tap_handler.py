#!/usr/bin/python3.9

# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary

# Standard library imports
import configparser
import os
import sys
import time

# Third-party imports
import boto3
from collections import namedtuple
from dotenv import load_dotenv

# Local project libraries
from dynamodb_controller import *
from utility.display_utils import *
from utility.file_utils import *
from utility.log_utils import *
from utility.signal_utils import *
from utility.utils import *


class TapHandler():

    def __init__(self):
        self.BATCH_SIZE = 10
        
        # Define file path constants
        FilePathConstants = namedtuple(
            "FilePathConstants",
            ["OPERATION_TAPS", "LAST_TAGS_AND_IDS", "FIFO_PATH"]
        )
        self.FILE_PATH_INFO = FilePathConstants(
            OPERATION_TAPS="/var/lib/screen/operation_taps.json",
            LAST_TAGS_AND_IDS="/var/lib/screen/last_tags_and_ids.json",
            FIFO_PATH="/tmp/screenPipe"
        )

        # Load environment variables
        load_dotenv()

        # Constants for Airtable configurations
        AirtableConstants = namedtuple("AirtableConstants", ["API_KEY"])
        self.AIRTABLE_CONST = AirtableConstants(
            API_KEY=os.getenv('AIRTABLE_API_KEY'))

        # Check for mandatory environment variables
        if not self.AIRTABLE_CONST.API_KEY:
            perror_log(f"[ERROR] [{__file__}] [TapHandler.__init__] - Environment variable not set. Context: {{AIRTABLE_CONST.API_KEY: {self.AIRTABLE_CONST.API_KEY}}}")
            raise ValueError("'AIRTABLE_API_KEY' is not set.")

        # Initialize signal handlers
        init_signal_handlers(["SIGTERM"])

        # Initialize database tap handler
        db_handler = DynamoDBTapHandler("API_Requests", self.FILE_PATH_INFO, self.BATCH_SIZE)

        # Initialize the display manager
        self.display_manager = DisplayManager()

    def handle_fifo_data(self, fifo_data, tags_and_ids, operation_taps, current_batch_count):
        fifo_data_split = fifo_data.split("::")
        program_name = fifo_data_split[0]
        tap_success = True

        # Handle operation taps
        if program_name == "operation_tap_listener.c":
            timestamp = fifo_data_split[1]
            push_success, operation_taps, current_batch_count = self.db_handler.handle_operation_tap(
                tags_and_ids,
                operation_taps,
                current_batch_count,
                timestamp
            )
            if not push_success:
                perror_log(f"[ERROR] [{__file__}] [TapHandler.handle_fifo_data] - Operation taps not registered. Context: {{fifo_data: {fifo_data}}}")
                tap_success = False
            save_json_to_file(self.FILE_PATH_INFO.OPERATION_TAPS, operation_taps)

        # Handle NFC taps
        elif program_name == "nfc_tap_listener.c":
            tag_uid = fifo_data_split[1].lower()
            timestamp = fifo_data_split[2]
            if not self.db_handler.handle_nfc_tap(tags_and_ids, tag_uid, timestamp):
                perror_log(f"[ERROR] [{__file__}] [TapHandler.handle_fifo_data] - NFC tap not registered. Context: {{fifo_data: {fifo_data}}}")
                tap_success = False

        # Handle invalid program names
        else:
            perror_log(f"[ERROR] [{__file__}] [TapHandler.handle_fifo_data] - Invalid program name. Context: {{program_name: {program_name}}}")
        
        return tap_success, tags_and_ids, operation_taps, current_batch_count
    
    def run(self):
        # Read the Airtable API key
        airtable_config = configparser.ConfigParser()
        airtable_config.read("/home/potato/.airtable/credentials.txt")

        # Print initialization logs
        print_log("Starting Screen.py")
        print_log("Pulling Previous Data")

        # Pull the last set of tags and IDs from the database
        is_update_success, tags_and_ids = self.db_handler.pull_latest_tags_and_ids()
        if not is_update_success:
            perror_log("Failed to update last_tags_and_ids from AWS database")
            sys.exit(0)

        # TODO: Figure out if we can make local ip static instead of dynamic
        # Push the latest local ip to the database
        is_push_success = self.db_handler.push_local_ip_to_db(tags_and_ids)
        if not is_push_success:
            perror_log("Failed to push local ip address to AWS database")
            sys.exit(0)

        # Load batched button presses from a file
        operation_taps = load_json_from_file(
            self.FILE_PATH_INFO.OPERATION_TAPS, 
            default_value={"Records": []}
        )

        # Update the current batch count based on the loaded tap data
        current_batch_count = len(operation_taps["Records"])

        print_log("Starting Display")

        try:
            while True:
                time.sleep(0.25)

                # Read data from the FIFO Pipe
                fifo_data = read_from_file(self.FILE_PATH_INFO.FIFO_PATH)
                if not fifo_data:
                    continue

                tap_success, tags_and_ids, operation_taps, current_batch_count = (
                    fifo_data, tags_and_ids, operation_taps, current_batch_count
                )

                # Save the last tags and IDs to a file
                save_json_to_file(
                    self.FILE_PATH_INFO.LAST_TAGS_AND_IDS, tags_and_ids)

                # Update the display with the background color indicating success or failure
                bg_color = (0, 170, 0) if tap_success else (0, 0, 255)
                self.display_manager.draw_display(tags_and_ids, bg_color=bg_color)         
        except KeyboardInterrupt:
            print_log("Program Interrupted")


if __name__ == "__main__":
    tap_handler = TapHandler()
    tap_handler.run()