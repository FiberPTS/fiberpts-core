import os

from dotenv import load_dotenv


script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)

load_dotenv(f"{script_dir}/../../.env.shared")

# File paths to named pipes
TOUCH_SENSOR_TO_SCREEN_PIPE: str = os.getenv('TOUCH_SENSOR_TO_SCREEN_PIPE')
NFC_TO_SCREEN_PIPE: str = os.getenv('NFC_TO_SCREEN_PIPE')

# File path to display framebuffer
DISPLAY_FRAME_BUFFER_PATH: str = os.getenv('DISPLAY_FRAME_BUFFER_PATH')
DISPLAY_FRAME_BUFFER_LOCK_PATH: str = os.getenv('DISPLAY_FRAME_BUFFER_LOCK_PATH')

# File path to device state
DEVICE_STATE_FILE_PATH: str = os.getenv('DEVICE_STATE_FILE_PATH')