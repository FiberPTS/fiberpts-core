import os
import time

from dotenv import load_dotenv
import supabase
from postgrest import APIResponse

from src.utils.touch_sensor_utils import Tap
from src.utils.utils import TIMESTAMP_FORMAT

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)

load_dotenv(f"{script_dir}/../../.env")

# TODO: Must first check if there is a record in devices table for the associated device_id and machine_name (can hardcode this)
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

    def insert_tap_data(self, tap: Tap) -> APIResponse:
        """Inserts a record with timestamp and device ID into the `tap_data` table.

        Args:
            tap: An instance of Tap containing the data to be inserted

        Returns:
            An APIResponse object representing the result of the database operation.
        """
        # TODO: Implement handling for connection issues.
        # TODO: Implement handling for authentication issues.
        # TODO: Implement data validation.
        # TODO: Implement handling for non-existent table.
        # TODO: Implement handling for non-existent device record.

        tap_record = {
            'timestamp': time.strftime(TIMESTAMP_FORMAT, time.localtime(tap.timestamp)),
            'device_id': tap.device_id
        }
        response = self.client.table('tap_data').insert(tap_record).execute()
        return response
