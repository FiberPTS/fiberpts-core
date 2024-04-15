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
from src.utils.screen_utils import read_device_state
from src.utils.paths import DEVICE_STATE_PATH
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

    def insert_tap_data(self, tap: Tap) -> bool:
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
        device_state = read_device_state(DEVICE_STATE_PATH)
        tap_record = {
            'timestamp': time.strftime(TIMESTAMP_FORMAT, time.localtime(tap.timestamp)),
            'device_id': tap.device_id
        }
        for key in ['order_id', 'employee_id', 'machine_id']:
            value = device_state.get(key, None)
            if value:
                tap_record[key] = value
        try:
            response = self.client.table('action_tap_data').insert(tap_record).execute()
            logger.info(response)  # TODO: Correctly print response (need to test)
            return True
        except httpx.NetworkError as e:
            logger.error(f"Network Error: {e}")
        return False

    def insert_employee_tap(self, employee_tap: NFCTag) -> bool:
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
        if employee_tap.type != NFCType.EMPLOYEE:
            logger.error("Invalid NFC Tag type. Expected EMPLOYEE.")
            return False
        employee_id = employee_tap.data.get('employee_id', None)
        if not employee_id:
            logger.error("Employee ID is missing.")
            return False
        employee_tap_record = {
            'timestamp': time.strftime(TIMESTAMP_FORMAT, time.localtime(employee_tap.timestamp)),
            'device_id': employee_tap.device_id,
            'employee_id': employee_id
        }
        machine_id_record = self.client.table("devices").select("machine_id").eq("device_id",
                                                                                 employee_tap.device_id).execute()
        machine_id = None if len(machine_id_record.data) == 0 else machine_id_record.data[0]['machine_id']
        if machine_id:
            employee_tap_record['machine_id'] = machine_id
        try:
            logger.info(employee_tap_record)
            response = self.client.table('employee_tap_data').insert(employee_tap_record).execute()
            logger.info(response)  # TODO: Correctly print response (need to test)
            return True
        except httpx.NetworkError as e:
            logger.error(f"Network Error: {e}")
        return False

    def insert_order_tap(self, order_tap: NFCTag) -> bool:
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
        if order_tap.type != NFCType.ORDER:
            logger.error("Invalid NFC Tag type. Expected ORDER.")
            return False
        logger.info('Inserting order tap record to Supabase')
        device_state = read_device_state(DEVICE_STATE_PATH)
        order_tap_record = {
            'timestamp': time.strftime(TIMESTAMP_FORMAT, time.localtime(order_tap.timestamp)),
            'device_id': order_tap.device_id,
            'order_id': order_tap.data['order_id']
        }
        employee_id = device_state.get('employee_id', None)
        if employee_id:
            order_tap_record['employee_id'] = employee_id
        machine_id_query = self.client.table("devices").select("machine_id").eq("device_id",
                                                                                order_tap.device_id).execute()
        machine_id_records = machine_id_query.data
        machine_id = None if len(machine_id_records) == 0 else machine_id_records[0]['machine_id']
        if machine_id:
            order_tap_record['machine_id'] = machine_id

        try:
            response = self.client.table('order_tap_data').insert(order_tap_record).execute()
            logger.info(response)  # TODO: Correctly print response (need to test)
            return True
        except httpx.NetworkError as e:
            logger.error(f"Network Error: {e}")
        return False

    def lookup_uid(self, uid: str) -> NFCTag:
        """Searches for an nfc record matching the unique id provided to it in Supabase.

        Args:
            uid: A string containing the unique id to be searched for

        Returns:
            A NFCTag object represnting either an employee or an order. Returns an NFCTag object represnting None if the operation fails. 
        """
        logger.info(f'Looking up NFC Tag: {uid} in Supabase')
        result = NFCTag(device_id=self.device_id, timestamp=time.time(), type=NFCType.NONE, data={}, tag_id=uid)
        try:
            order_tag_query = self.client.table("order_tags").select("order_tag_group_id").eq("tag_id", uid).execute()
            order_tag_records = order_tag_query.data
            logger.info(f"Order Tags: {order_tag_records}")
            if len(order_tag_records) > 0:
                order_tag_group_id = order_tag_records[0]["order_tag_group_id"]
                order_query = self.client.table("order_tag_groups").select("order_id").eq(
                    "group_id", order_tag_group_id).execute()
                order_records = order_query.data
                if len(order_records) > 0:
                    order_record = order_records[0]
                    result = NFCTag(device_id=self.device_id,
                                    timestamp=time.time(),
                                    type=NFCType.ORDER,
                                    data=order_record,
                                    tag_id=uid)
                else:
                    logger.info("Could not find the order group associated with this NFC tag.")
            else:
                employee_tag_query = self.client.table("employee_tags").select("employee_id").eq("tag_id",
                                                                                                 uid).execute()
                employee_tag_records = employee_tag_query.data
                logger.info(f"Employee Tags: {employee_tag_records}")
                if len(employee_tag_records) > 0:
                    employee_id = employee_tag_records[0]["employee_id"]
                    employee_query = self.client.table("employees").select("name, employee_id").eq(
                        "employee_id", employee_id).execute()
                    employee_records = employee_query.data
                    if len(employee_records) > 0:
                        employee_record = employee_records[0]
                        result = NFCTag(device_id=self.device_id,
                                        timestamp=time.time(),
                                        type=NFCType.EMPLOYEE,
                                        data=employee_record,
                                        tag_id=uid)
                    else:
                        logger.info("Could not find the employee associated with this NFC tag.")
        except httpx.NetworkError as e:
            logger.error(f"Network Error: {e}")
        if result.type == NFCType.NONE:
            logger.info("Could not find any employee or order associated with this NFC tag.")
        return result

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
