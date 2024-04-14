import os
import time
import logging
import logging.config

from dotenv import load_dotenv
import supabase
from postgrest import APIResponse
import httpx

from src.utils.touch_sensor_utils import Tap
from src.utils.utils import NFCType, get_device_id
from src.utils.nfc_reader_utils import NFCTag
from src.utils.utils import TIMESTAMP_FORMAT
from src.utils.paths import PROJECT_DIR

load_dotenv(f"{PROJECT_DIR}/.env")
logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])


class CloudDBClient:
    """Client for interacting with a cloud database using the Supabase API.
    
    Attributes:
        url: A string representing the URL of the database.
        key: A string representing the API key for the database.
        client: Supabase Client instance.
    """

    def __init__(self):
        """Initializes the client with database credentials.

        Args:
            None
        
        Returns:
            None
        """
        url = os.getenv('DATABASE_URL')
        key = os.getenv('DATABASE_API_KEY')
        self.client = supabase.create_client(url, key)
        self.device_id = get_device_id()


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
        logger.info('Inserting device record to Supabase')  # TODO: Correctly print response (need to test)
        # TODO: Check if device_id already exists
        # TODO: How can I check whether the device id was created based on the response
        device_record = {'device_id': device_id, 'name': ''}
        response = self.client.table('devices').insert(device_record).execute()
        logger.info(response)  # TODO: Correctly print response (need to test)
        return response

    def get_new_device_id(self) -> str:
        """Generates a new, unique device ID for a new device.

        The function retrieves the highest current device ID from the 'devices'
        table, increments it by one, and formats it to maintain consistent ID
        structure. If no device IDs are present in the table, it starts
        numbering from 'fpts-001'.

        Args:
            None
    
        Returns:
            A string representing the newly generated device ID.
        """
        response = self.client.table('devices') \
            .select('device_id') \
            .order('device_id', desc=True) \
            .limit(1) \
            .execute()
        # TODO: Find a better way to handle this since assuming the first record is unallocated is risky
        device_id = ''
        if not response:
            device_id = 'fpts-001'
        else:
            # Extract numeric part of device ID, increment it, and format it
            id_num = '{:03d}'.format(int(response.data[0]['device_id'][-3:]) + 1)
            device_id = 'fpts-' + id_num
        return device_id
    
    def insert_employee_tap(self, employee_tap: NFCTag) -> int:
        """Inserts a new employee tap record into the `employee_tap_data` table.

        Args:
            employee_tag: An instance of NFCTag containing the employee tap to be inserted

        Returns:
            An int value representing the success (0) or failure (-1) of the database operation.
        """
        # TODO: Implement handling for connection issues.
        # TODO: Implement handling for authentication issues.
        # TODO: Implement data validation.
        # TODO: Implement handling for non-existent table.
        # TODO: Implement handling for non-existent device record.
        logger.info('Inserting employee tap record to Supabase')
        employee_tap_record = {
            'timestamp': time.strftime(TIMESTAMP_FORMAT, time.localtime(employee_tap.timestamp)),
            'device_id': employee_tap.device_id,
            'employee_unifi_id': employee_tap.data['unifi_id']
        }

        try:
            response = self.client.table('employee_tap_data').insert(employee_tap_record).execute()
            logger.info(response)  # TODO: Correctly print response (need to test)
        except httpx.NetworkError as e:
            logger.error(f"Network Error: {e}")
            return -1
        return 0
    
    def insert_order_tap(self, order_tap: NFCTag) -> int:
        """Inserts a new order tap record into the `order_tap_data` table.

        Args:
            order_tag: An instance of NFCTag containing the order tap to be inserted

        Returns:
            An int value representing the success (0) or failure (-1) of the database operation.
        """
        # TODO: Implement handling for connection issues.
        # TODO: Implement handling for authentication issues.
        # TODO: Implement data validation.
        # TODO: Implement handling for non-existent table.
        # TODO: Implement handling for non-existent device record.
        logger.info('Inserting order tap record to Supabase')
        order_tap_record = {
            'timestamp': time.strftime(TIMESTAMP_FORMAT, time.localtime(order_tap.timestamp)),
            'device_id': order_tap.device_id
        }
        try:
            response = self.client.table('order_tap_data').insert(order_tap_record).execute()
            logger.info(response)  # TODO: Correctly print response (need to test)
        except httpx.NetworkError as e:
            logger.error(f"Network Error: {e}")
            return -1
        return 0

    
    def lookup_uid(self, uid: str):
        """Searches for an nfc record matching the unique id provided to it in Supabase.

        Args:
            uid: A string containing the unique id to be searched for

        Returns:
            A NFCTag object represnting either an employee or an order. Returns an NFCTag object represnting None if the operation fails. 
        """
        logger.info(f'Looking up uid: {uid} in Supabase')
        result = NFCTag(device_id = self.device_id,
                        timestamp = time.time(),
                        type = NFCType.NONE,
                        data = {},
                        tag_id = uid
                        )
        try:
            order_tag_records = self.client.table("order_tags").select("order_tag_group_id").eq("tag_id", uid).execute()
            if len(order_tag_records.data) > 0:
                order_tag_group_id = order_tag_records.data[0]["order_tag_group_id"]
                order_records = self.client.table("order_tag_groups").select("order_id").eq("group_id",order_tag_group_id).execute()
                if len(order_records.data) > 0:
                    order_data = order_records.data[0]
                    result = NFCTag(device_id = self.device_id,
                                    timestamp = time.time(),
                                    type = NFCType.ORDER,
                                    data = order_data,
                                    tag_id = uid
                                    )
                else:
                    logger.info("Could not find the order group associated with this tag.")
            else:
                employee_tag_records = self.client.table("employee_tags").select("employee_unifi_id").eq("tag_id", uid).execute()
                if len(employee_tag_records.data) > 0:
                    employee_unit_id = employee_tag_records[0]["Employee_Unit_ID"]
                    employee = self.client.table("employees").select("name, unifi_id").eq("unifi_id", employee_unit_id).execute()
                    employee_data = employee.data[0]
                    result = NFCTag(device_id = self.device_id,
                                    timestamp = time.time(),
                                    type = NFCType.EMPLOYEE,
                                    data = employee_data,
                                    tag_id = uid
                                    )
                else:
                    logger.info("Could not find any employee or order associated with this NFC Tag.")
        except httpx.NetworkError as e:
            logger.error(f"Network Error: {e}")
        return result
