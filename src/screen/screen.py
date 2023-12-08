# Standard library imports
import time

# Third-party imports
from PIL import Image, ImageDraw, ImageFont

# Application specific imports
from config.screen_config import *
from src.utils.env_variables import (TOUCH_SENSOR_TO_SCREEN_PIPE, 
                                     DISPLAY_FRAME_BUFFER_PATH, 
                                     DEVICE_STATE_FILE_PATH)
from src.utils.screen_utils import (ftimestamp, 
                                    read_device_state, 
                                    write_device_state, 
                                    read_pipe, 
                                    write_image_to_fb)


class Screen:
    """
    A class to manage and display the user interface on a screen.

    This class handles drawing text, images, and popups to a screen, including rotating the display for correct orientation. It manages the screen's framebuffer for rendering, reads touch sensor data through a named pipe, and updates the display based on the incoming data.

    Attributes:
        display_fb_path (str): Path to the display framebuffer.
        display_height (int): Height of the display in pixels.
        display_width (int): Width of the display in pixels.
        display_frame_rate (int): Frame rate for display updates.
        dashboard_font_family (str): Font family for the dashboard text.
        dashboard_font_size (int): Font size for the dashboard text.
        dashboard_font_color (str): Color of the dashboard text.
        dashboard_bg_color (str): Background color of the dashboard.
        popup_font_family (str): Font family for popup messages.
        popup_font_size (int): Font size for popup messages.
        popup_font_color (str): Color of the popup message text.
        popup_error_bg_color (str): Background color for error popups.
        popup_warning_bg_color (str): Background color for warning popups.
        popup_duration (int): Duration to display popups (in seconds).
        tap_event_bg_color (str): Background color for tap event messages.
        order_set_bg_color (str): Background color for order set messages.
        employee_set_bg_color (str): Background color for employee set messages.
        popup_error_message (str): Default message for error popups.
        popup_warning_message (str): Default message for warning popups.
        tap_event_message (str): Default message for tap event notifications.
        order_set_message (str): Default message for order set notifications.
        employee_set_message (str): Default message for employee set notifications.
        touch_sensor_pipe (str): Path to the named pipe for touch sensor data.
        device_state_file_path (str): Path to the file for storing device state.

    The class uses PIL for image creation and manipulation and communicates with the touch sensor module via a named pipe.
    """

    def __init__(
            self,
            display_fb_path: str = DISPLAY_FRAME_BUFFER_PATH,
            display_height: int = DISPLAY_HEIGHT,
            display_width: int = DISPLAY_WIDTH,
            display_frame_rate: int = DISPLAY_FRAME_RATE,
            dashboard_font_family: str = DASHBOARD_FONT_FAMILY,
            dashboard_font_size: int = DASHBOARD_FONT_SIZE,
            dashboard_font_color: str = DASHBOARD_FONT_COLOR,
            dashboard_bg_color: str = DASHBOARD_BG_COLOR,
            popup_font_family: str = POPUP_FONT_FAMILY,
            popup_font_size: int = POPUP_FONT_SIZE,
            popup_font_color: str = POPUP_FONT_COLOR,
            popup_error_bg_color: str = POPUP_ERROR_BG_COLOR,
            popup_warning_bg_color: str = POPUP_ERROR_BG_COLOR,
            popup_duration: int = POPUP_DURATION,
            tap_event_bg_color: str = TAP_EVENT_BG_COLOR,
            order_set_bg_color: str = ORDER_SET_BG_COLOR,
            employee_set_bg_color: str = EMPLOYEE_SET_BG_COLOR,
            popup_error_message: str = POPUP_ERROR_MESSAGE,
            popup_warning_message: str = POPUP_WARNING_MESSAGE,
            tap_event_message: str = TAP_EVENT_MESSAGE,
            order_set_message: str = ORDER_SET_MESSAGE,
            employee_set_message: str = EMPLOYEE_SET_MESSAGE,
            touch_sensor_pipe: str = TOUCH_SENSOR_TO_SCREEN_PIPE,
            device_state_file_path: str = DEVICE_STATE_FILE_PATH
    ) -> None:
        """
        Initialize the Screen instance with the specified display properties, font settings, and file paths.

        This method sets up the screen attributes and initializes the display with the default dashboard view.

        Args:
            display_fb_path (str): Path to the framebuffer device for the display.
            display_height (int): The height of the display in pixels.
            display_width (int): The width of the display in pixels.
            display_frame_rate (int): The refresh rate at which the screen updates.
            dashboard_font_family (str): Font family for dashboard text.
            dashboard_font_size (int): Font size for dashboard text.
            dashboard_font_color (str): Color for dashboard text.
            dashboard_bg_color (str): Background color for the dashboard area.
            popup_font_family (str): Font family for popup message text.
            popup_font_size (int): Font size for popup message text.
            popup_font_color (str): Color for popup message text.
            popup_error_bg_color (str): Background color for error popups.
            popup_warning_bg_color (str): Background color for warning popups.
            popup_duration (int): Duration in seconds for which popups are displayed.
            tap_event_bg_color (str): Background color for tap event notifications.
            order_set_bg_color (str): Background color for order set notifications.
            employee_set_bg_color (str): Background color for employee set notifications.
            popup_error_message (str): Default message displayed in error popups.
            popup_warning_message (str): Default message displayed in warning popups.
            tap_event_message (str): Default message for tap event notifications.
            order_set_message (str): Default message for order set notifications.
            employee_set_message (str): Default message for employee set notifications.
            touch_sensor_pipe (str): Path to the named pipe for receiving touch sensor data.
            device_state_file_path (str): Path to the file where device state is stored.
        """
        # Display attributes
        self.display_fb_path = display_fb_path
        self.display_height = display_height
        self.display_width = display_width
        self.display_frame_rate = display_frame_rate
        # Dashboard attributes
        self.dashboard_font_family = dashboard_font_family
        self.dashboard_font_size = dashboard_font_size
        self.dashboard_font_color = dashboard_font_color
        self.dashboard_bg_color = dashboard_bg_color
        # Popup attributes
        self.popup_font_family = popup_font_family
        self.popup_font_size = popup_font_size
        self.popup_font_color = popup_font_color
        self.popup_error_bg_color = popup_error_bg_color
        self.popup_warning_bg_color = popup_warning_bg_color
        self.popup_duration = popup_duration
        # Event attributes
        self.tap_event_bg_color = tap_event_bg_color
        self.order_set_bg_color = order_set_bg_color
        self.employee_set_bg_color = employee_set_bg_color
        # Message attributes
        self.popup_error_message = popup_error_message
        self.popup_warning_message = popup_warning_message
        self.tap_event_message = tap_event_message
        self.order_set_message = order_set_message
        self.employee_set_message = employee_set_message
        # File paths
        self.touch_sensor_pipe = touch_sensor_pipe
        self.device_state_file_path = device_state_file_path
        # Initialize screen
        self.device_state = self.read_device_state(device_state_file_path)
        self.image = None
        self.clear_display()
    
    def get_image_center(self) -> tuple[int, int]:
        """
        Get the center coordinates of the current image.

        Returns:
            tuple[int, int]: The center coordinates (x, y) of the image, or (-1, -1) if no image is set.
        """
        if self.image:
            width, height = self.image.size
            center_x, center_y = width//2, height//2
            return (center_x, center_y)
        return (-1,-1)

    def create_image(self, bg_color: str) -> None:
        """
        Create an image with the specified background color (assumes the screen needs 90 degree rotation).

        Args:
            bg_color (str): Background color for the image.
        """
        self.image = Image.new('RGB', (self.display_height, self.display_width), bg_color)

    def draw_image(self) -> None:
        """
        Draw the current image to the display (assumes the screen needs 90 degree rotation).
        """
        if self.image:
            self.image = self.image.rotate(90, expand=True)
            write_image_to_fb(self.image, self.display_fb_path)
        self.image = None
    
    def clear_display(self) -> None:
        """
        Clear the display by setting it to the dashboard background color.
        """
        self.create_image(self.dashboard_bg_color)
        self.draw_image()

    def add_text(self, text: str, position: tuple[int, int], font_family: str, font_size: int, font_color: str, centered: bool = False) -> None:
        """
        Add text to the current image at the specified position.

        Args:
            text (str): The text to be added.
            position (tuple[int, int]): The position (x, y) where the text will be added.
            font_family (str): The font family to be used for the text.
            font_size (int): The font size of the text.
            font_color (str): The color of the text.
            centered (bool): If True, centers the text at the given position.
        """
        if self.image:
            draw = ImageDraw.Draw(self.image)
            font = ImageFont.truetype(font_family, font_size)
            if centered:
                # Calculate text size
                text_width, text_height = draw.textsize(text, font=font)
                position = (position[0]-text_width//2, position[1]-text_height//2)
            draw.text(position, text, font=font, fill=font_color)

    def draw_dashboard(self) -> None:
        """
        Draw the dashboard interface on the screen.
        """
        self.create_image(self.dashboard_bg_color)
        image_center = self.get_image_center()
        self.add_text(f"Date: {ftimestamp(time.time())}", (0, 0), self.dashboard_font_family, self.dashboard_font_size, self.dashboard_font_color, centered=False)
        self.add_text(f"Unit Count: {self.device_state['unit_count']}", image_center, self.dashboard_font_family, self.dashboard_font_size, self.dashboard_font_color, centered=True)
        self.draw_image()

    def draw_popup(self, text: str, bg_color: str) -> None:
        """
        Draw a popup message on the screen with specified text and background color.

        Args:
            text (str): The message text to display in the popup.
            bg_color (str): The background color for the popup.
        """
        self.create_image(bg_color)
        image_center = self.get_image_center()
        self.add_text(text, image_center, self.popup_font_family, self.popup_font_size, self.popup_font_color, centered=True)
        self.draw_image()
        time.sleep(self.popup_duration)

    def handle_pipe_data(self) -> None:
        """
        Handle data received from the touch sensor pipe. Updates device state and draws popups based on the received data.
        """
        is_pipe_empty = False
        while not is_pipe_empty:
            tap_data = read_pipe(self.touch_sensor_pipe)
            if tap_data:
                # TODO: Decide if this data is or will be useful
                # device_id = tap_data["device_id"]
                # timestamp = tap_data["timestamp"]
                status = tap_data['status']  # This will be either "GOOD" or "BAD"
                if status == 'Bad':
                    self.draw_popup(self.popup_warning_message, self.popup_warning_bg_color)
                elif status == 'Good':
                    self.device_state['unit_count'] += 1
                    write_device_state(self.device_state, self.device_state_file_path)
                    self.draw_popup(self.tap_event_message, self.tap_event_bg_color)
            else:
                is_pipe_empty = True

    def start(self) -> None:
        """
        Start the main loop of the screen, updating the display at the set frame rate and handling incoming pipe data.
        """
        frame_duration = 1.0 / self.display_frame_rate
        while True:
            start_time = time.time()
            self.draw_dashboard()
            elapsed_time = time.time() - start_time
            time.sleep(max(0, frame_duration - elapsed_time))
            self.handle_pipe_data()


if __name__ == "__main__":
    screen = Screen()
    screen.start()
