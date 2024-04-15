import time
import os
import logging
import logging.config
import threading
from queue import Queue

from PIL import Image, ImageDraw, ImageFont

from config.screen_config import *
from src.utils.paths import (TOUCH_SENSOR_TO_SCREEN_PIPE, NFC_READER_TO_SCREEN_PIPE, DEVICE_STATE_PATH, PROJECT_DIR)
from src.utils.screen_utils import (DisplayAttributes,
                                    DashboardAttributes,
                                    PopupAttributes,
                                    read_device_state,
                                    write_device_state,
                                    is_at_least_next_day,
                                    get_image_center,
                                    read_pipe,
                                    write_image_to_fb)
from src.utils.utils import (TapStatus, NFCType)


SAVED_TIMESTAMP_FORMAT = '%Y-%m-%d'

logging.config.fileConfig(f"{PROJECT_DIR}/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(os.path.basename(__file__).split('.')[0])


class Screen:
    """This class handles drawing text, images, and popups to a screen. 
    
    Additionally, it handles functionality for rotating the display for correct orientation, managing the screen's framebuffer for rendering, 
    reading touch sensor data through a named pipe, and updating the display based on the incoming data.

    Attributes:
        display_attributes (DisplayAttributes): Attributes related to display properties like framebuffer path, height, width, and frame rate.
        dashboard_attributes (DashboardAttributes): Attributes related to dashboard appearance such as font family, size, color, and background color.
        popup_attributes (PopupAttributes): Attributes for configuring popups, including fonts, colors, and duration.
        popup_queue (Queue): A queue for all popup data.
        image: Current image being displayed on the screen.
    """

    def __init__(self) -> None:
        """Initialize the Screen instance with the specified display properties and settings.
        
        Args:
            None

        Returns:
            None
        """
        # Configurations
        self.display_attributes = DisplayAttributes()
        self.dashboard_attributes = DashboardAttributes()
        self.popup_attributes = PopupAttributes()
        # Initialize screen
        self.popup_queue = Queue()
        self.touch_sensor_pipe_queue = Queue()
        self.nfc_reader_pipe_queue = Queue()
        self.image = None
        self.create_image(self.dashboard_attributes.dashboard_bg_color)
        self.device_state_lock = threading.Lock()

    def create_image(self, bg_color: str) -> None:
        """Create an image with the specified background color (assumes the screen needs 90 degree rotation).

        Args:
            bg_color (str): Background color for the image.

        Returns:
            None
        """
        self.image = Image.new('RGB', (self.display_attributes.display_height, self.display_attributes.display_width),
                               bg_color)

    def draw_image(self) -> None:
        """Draw the current image to the display (assumes the screen needs 90 degree rotation).
        
        Args:
            None
        
        Returns:
            None
        """
        if self.image:
            self.image = self.image.rotate(90, expand=True)
            write_image_to_fb(self.image, self.display_attributes.display_fb_path,
                              self.display_attributes.display_fb_lock_path)

    def add_text(self,
                 text: str,
                 position: tuple[int, int],
                 font_family: str,
                 font_size: int,
                 font_color: str,
                 centered: bool = False) -> None:
        """Add text to the current image at the specified position.

        Args:
            text (str): The text to be added.
            position (tuple[int, int]): The position (x, y) where the text will be added.
            font_family (str): The font family to be used for the text.
            font_size (int): The font size of the text.
            font_color (str): The color of the text.
            centered (bool): If True, centers the text at the given position.
        
        Returns:
            None
        """
        if self.image:
            draw = ImageDraw.Draw(self.image)
            font = ImageFont.truetype(font_family, font_size)
            if centered:
                ascent, descent = font.getmetrics()
                bbox = font.getbbox(text)
                text_width, text_height = bbox[2] - bbox[0], ascent + descent
                position = (position[0] - text_width // 2, position[1] - text_height // 2)
            draw.text(position, text, font=font, fill=font_color)

    def draw_dashboard(self) -> None:
        """Draw the dashboard interface on the screen.
        
        Args:
            None

        Returns:
            None
        """
        self.create_image(self.dashboard_attributes.dashboard_bg_color)
        image_center = get_image_center(self.image)
        current_time = time.time()
        date_str = time.strftime(SAVED_TIMESTAMP_FORMAT, time.localtime(current_time))
        self.add_text(date_str, (0, 0),
                      self.dashboard_attributes.dashboard_font_family,
                      self.dashboard_attributes.dashboard_font_size,
                      self.dashboard_attributes.dashboard_font_color,
                      centered=False)
        device_state = read_device_state(DEVICE_STATE_PATH)
        saved_timestamp = device_state.get('saved_timestamp', None)
        if not saved_timestamp or is_at_least_next_day(saved_timestamp, current_time):
            device_state['unit_count'] = 0
            device_state['employee_id'], device_state['order_id'], device_state['employee_name'] = (None, None, None)
        write_device_state(device_state, DEVICE_STATE_PATH)
        unit_count = device_state.get('unit_count', 0)
        self.add_text(f"Unit Count: {unit_count}",
                      image_center,
                      self.dashboard_attributes.dashboard_font_family,
                      self.dashboard_attributes.dashboard_font_size,
                      self.dashboard_attributes.dashboard_font_color,
                      centered=True)
        employee_name = device_state.get('employee_name', None)
        if employee_name:
            self.add_text(employee_name, (0, self.display_attributes.display_width - 30),
                          self.dashboard_attributes.dashboard_font_family,
                          self.dashboard_attributes.dashboard_font_size,
                          self.dashboard_attributes.dashboard_font_color,
                          centered=False)
        order_id = device_state.get('order_id', None)
        if order_id:
            self.add_text(order_id, (0, self.display_attributes.display_width - 60),
                          self.dashboard_attributes.dashboard_font_family,
                          self.dashboard_attributes.dashboard_font_size,
                          self.dashboard_attributes.dashboard_font_color,
                          centered=False)
        self.draw_image()

    def draw_popup(self, text: str, bg_color: str) -> None:
        """Draw a popup message on the screen with specified text and background color.

        Args:
            text (str): The message text to display in the popup.
            bg_color (str): The background color for the popup.
        
        Returns:
            None
        """
        self.create_image(bg_color)
        image_center = get_image_center(self.image)
        self.add_text(text,
                      image_center,
                      self.popup_attributes.message_attributes.popup_font_family,
                      self.popup_attributes.message_attributes.popup_font_size,
                      self.popup_attributes.message_attributes.popup_font_color,
                      centered=True)
        self.draw_image()
        time.sleep(self.popup_attributes.popup_duration)

    def handle_pipe_data(self) -> None:
        """Handle data received from the touch sensor pipe. Updates device state and queues popups based on the received data.
        
        Args:
            None

        Returns:
            None
        """
        if not self.touch_sensor_pipe_queue.empty():
            tap_data = self.touch_sensor_pipe_queue.get()
            logger.info('Tap received by screen')
            # TODO: We may decide to store this data from a stopwatch time.
            # timestamp = tap_data["timestamp"]
            popup_item = None
            status = TapStatus[tap_data['status']]
            if status == TapStatus.GOOD:
                device_state = read_device_state(DEVICE_STATE_PATH)
                device_state['unit_count'] += 1
                write_device_state(device_state, DEVICE_STATE_PATH)
                popup_item = (self.popup_attributes.message_attributes.tap_event_message,
                              self.popup_attributes.event_attributes.tap_event_bg_color)
            elif status == TapStatus.BAD and self.popup_queue.qsize() < POPUP_LIMIT:
                popup_item = (self.popup_attributes.message_attributes.popup_warning_message,
                              self.popup_attributes.event_attributes.popup_warning_bg_color)
            if popup_item:
                self.popup_queue.put(popup_item)
        if not self.nfc_reader_pipe_queue.empty():
            nfc_data = self.nfc_reader_pipe_queue.get()
            logger.info('NFC data received by screen')
            tag_data, nfc_type = nfc_data['data'], NFCType[nfc_data['type']]
            popup_item = None
            device_state = read_device_state(DEVICE_STATE_PATH)
            if nfc_type == NFCType.NONE and self.popup_queue.qsize() < POPUP_LIMIT:
                popup_item = (self.popup_attributes.message_attributes.popup_error_message,
                              self.popup_attributes.event_attributes.popup_error_bg_color)
            elif nfc_type == NFCType.EMPLOYEE:
                employee_id, employee_name = tag_data.get('employee_id', None), tag_data.get('name', None)
                # Reset unit count if employee changes
                if employee_id:
                    if employee_id == device_state.get('employee_id', None):
                        popup_item = (self.popup_attributes.message_attributes.employee_same_message,
                                      self.popup_attributes.event_attributes.employee_same_bg_color)
                    else:
                        device_state['unit_count'] = 0
                        popup_item = (self.popup_attributes.message_attributes.employee_set_message,
                                      self.popup_attributes.event_attributes.employee_set_bg_color)
                    device_state['employee_id'], device_state['employee_name'] = (employee_id, employee_name)
            elif nfc_type == NFCType.ORDER:
                order_id = tag_data.get('order_id', None)
                # Reset unit count if order changes
                if order_id:
                    if order_id == device_state.get('order_id', None):
                        popup_item = (self.popup_attributes.message_attributes.order_same_message,
                                      self.popup_attributes.event_attributes.order_same_bg_color)
                    else:
                        device_state['unit_count'] = 0
                        device_state['order_id'] = order_id
                        popup_item = (self.popup_attributes.message_attributes.order_set_message,
                                      self.popup_attributes.event_attributes.order_set_bg_color)
            if popup_item:
                self.popup_queue.put(popup_item)
            write_device_state(device_state, DEVICE_STATE_PATH)

    def manage_display(self) -> None:
        """Manages writing popups to the screen using the popup queue and draws the dashboard to the display at the set frame rate after each popup.

        Args:
            None

        Returns:
            None
        """
        frame_duration = 1.0 / self.display_attributes.display_frame_rate
        while True:
            self.draw_dashboard()
            text, bg_color = self.popup_queue.get()
            self.draw_popup(text, bg_color)
            time.sleep(frame_duration)

    def manage_touch_sensor_pipe(self) -> None:
        """Manages reading data from the touch sensor pipe and queues it for the main thread to process.
        
        Args:
            None
        
        Returns:
            None
        """
        while True:
            tap_data = read_pipe(TOUCH_SENSOR_TO_SCREEN_PIPE)
            if tap_data:
                self.touch_sensor_pipe_queue.put(tap_data)

    def manage_nfc_reader_pipe(self) -> None:
        """Manages reading data from the NFC reader pipe and queues it for the main thread to process.
        
        Args:
            None
        
        Returns:
            None
        """
        while True:
            nfc_data = read_pipe(NFC_READER_TO_SCREEN_PIPE)
            if nfc_data:
                self.nfc_reader_pipe_queue.put(nfc_data)

    def start_threads(self) -> None:
        """Creates and starts the display thread and pipe-reading threads.
        
        Args:
            None
        
        Returns:
            None
        """
        # Initialize display thread
        display_thread = threading.Thread(target=self.manage_display)
        display_thread.daemon = True  # Exit display thread when main process exits
        display_thread.start()

        # Initialize pipe-reading threads
        touch_sensor_pipe_thread = threading.Thread(target=self.manage_touch_sensor_pipe)
        touch_sensor_pipe_thread.daemon = True
        touch_sensor_pipe_thread.start()

        nfc_reader_pipe_thread = threading.Thread(target=self.manage_nfc_reader_pipe)
        nfc_reader_pipe_thread.daemon = True
        nfc_reader_pipe_thread.start()

    def run(self) -> None:
        """Starts the main loop of the screen and handles incoming pipe data for the display thread.
        
        Args:
            None
        
        Returns:
            None
        """
        logger.info('Running main loop')
        self.start_threads()
        while True:
            self.handle_pipe_data()



if __name__ == "__main__":
    logger.info('Starting screen.py')
    screen = Screen()
    screen.run()
