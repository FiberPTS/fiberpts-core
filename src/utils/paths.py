import os

from dotenv import load_dotenv


script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)

load_dotenv(f"{script_dir}/../../.env.shared")

# File paths to named pipes
TOUCH_SENSOR_TO_SCREEN_PIPE = os.getenv('TOUCH_SENSOR_TO_SCREEN_PIPE')
NFC_TO_SCREEN_PIPE = os.getenv('NFC_TO_SCREEN_PIPE')

# File path to display framebuffer
DISPLAY_FRAME_BUFFER_PATH = os.getenv('DISPLAY_FRAME_BUFFER_PATH')

# File path to device state
DEVICE_STATE_FILE_PATH = os.getenv('DEVICE_STATE_FILE_PATH')