import os
import time
import logging
import logging.config

from dotenv import load_dotenv
import supabase
from postgrest import APIResponse
import httpx

from src.utils.touch_sensor_utils import Tap
from src.utils.utils import TIMESTAMP_FORMAT
from src.utils.paths import PROJECT_DIR

load_dotenv(f"{PROJECT_DIR}/.env")
logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])

class CloudDBClient:
    """Client for interacting with a cloud database using the Supabase API."""

    def __init__(self):
        """Initializes the client with database credentials.

        Attributes:
            client: Supabase Client instance.
        """
        url = os.getenv('DATABASE_URL')
        key = os.getenv('DATABASE_API_KEY')
        self.client = supabase.create_client(url, key)

    def insert_tap_data(self, tap: Tap) -> int:
        """Inserts a new tap data record into the `tap_data` table.

        Args:
            tap: An instance of Tap containing the data to be inserted

        Returns:
            An int value representing the success (0) or failure (-1) of the database operation.
        """
        # TODO: Implement handling for connection issues.
        # TODO: Implement handling for authentication issues.
        # TODO: Implement data validation.
        # TODO: Implement handling for non-existent table.
        # TODO: Implement handling for non-existent device record.
        logger.info('Inserting tap record to Supabase')
        tap_record = {
            'timestamp': time.strftime(TIMESTAMP_FORMAT, time.localtime(tap.timestamp)),
            'device_id': tap.device_id
        }
        try:
            response = self.client.table('tap_data').insert(tap_record).execute()
            logger.info(response)  # TODO: Correctly print response (need to test)
        except httpx.NetworkError as e:
            logger.error(f"Network Error: {e}")
            return -1
        return 0

    def insert_device_data(self, device_id: str) -> APIResponse:
        """Inserts a new device record into the 'devices' table.

        Before insertion, it checks if the device ID already exists to avoid duplicates.
        After insertion, the response can be used to confirm whether the device was successfully created.

        Args:
            device_id: A string representing the unique device ID to be inserted.

        Returns:
            An APIResponse object representing the result of the database operation.
        """
        logger.info('Insertting device record to Supabase')  # TODO: Correctly print response (need to test)
        # TODO: Check if device_id already exists
        # TODO: How can I check whether the device id was created based on the response
        device_record = {
            'device_id': device_id,
            'name': ''
        }
        response = self.client.table('devices').insert(device_record).execute()
        logger.info(response)  # TODO: Correctly print response (need to test)
        return response

    def get_new_device_id(self):
        """Generates a new, unique device ID for a new device.

        The function retrieves the highest current device ID from the 'devices'
        table, increments it by one, and formats it to maintain consistent ID
        structure. If no device IDs are present in the table, it starts
        numbering from 'fpts-001'.

        Returns:
            A string representing the newly generated device ID.
        """
        response = self.client.table('devices') \
            .select('device_id') \
            .order('device_id', desc=True) \
            .limit(1) \
            .execute()

        device_id = ''
        if not response:
            device_id = 'fpts-001'
        else:
            # Extract numeric part of device ID, increment it, and format it
            id_num = '{:03d}'.format(int(response.data[0]['device_id'][-3:]) + 1)
            device_id = 'fpts-' + id_num
        return device_id
