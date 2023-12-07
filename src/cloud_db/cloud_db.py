import os

from dotenv import load_dotenv
from supabase import create_client, APIResponse


load_dotenv()


class CloudDBClient:

    def __init__(self):
        url = os.getenv('DATABASE_URL')
        key = os.getenv('DATABASE_API_KEY')
        self.client = create_client(url, key)
    
    def insert_tap_data_entry(self, table: str, data: dict) -> ...:
        pass
