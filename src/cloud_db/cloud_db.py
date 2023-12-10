import os

from dotenv import load_dotenv
import supabase
from postgrest import APIResponse

from touch_sensor.touch_sensor import Tap
from utils.touch_sensor_utils import tap_to_db_entry

load_dotenv()


class CloudDBClient:
    """Client for interacting with a cloud database using the Supabase API."""

    def __init__(self):
        """
        Initializes the client with database credentials.

        Attributes:
            client: Supabase Client instance.
        """
        url = os.getenv('DATABASE_URL')
        key = os.getenv('DATABASE_API_KEY')
        self.client = supabase.create_client(url, key)
    
    def insert_tap_data(self, tap_record: dict) -> APIResponse:
        """
        Inserts tap data (timestamp and machine ID) into the database.

        Args:
            tap_record: A dict containing the data to be inserted.

        Returns:
            An APIResponse object representing the result of the database operation.
        """
        # TODO: Implement handling for connection issues.
        # TODO: Implement handling for authentication issues.
        # TODO: Implement data validation.
        # TODO: Implement handling for non-existent table.
        response = self.client.table('tap_data').insert(tap_record).execute()
        return response
