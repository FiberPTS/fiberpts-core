from PIL import Image, ImageDraw, ImageFont
import numpy as np
from .utils import *


# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary


def write_to_framebuffer(data, fb_path):
    """
    Writes data to the framebuffer device.

    Args:
        data (np.array): The data to write.
        fb_path (string): The file path to the frame buffer

    Returns:
        None
    """
    with open(fb_path, "wb") as f:
        f.write(data.tobytes())


def image_to_rgb565(image):
    """
    Converts a PIL Image to RGB565 format.

    Args:
        image (PIL.Image): The image object.

    Returns:
        np.array: The image data in RGB565 format.
    """
    r, g, b = image.split()  # Split into R, G, B channels
    r, g, b = np.array(r, dtype=np.uint16), np.array(g, dtype=np.uint16), np.array(b, dtype=np.uint16)  # Convert to np arrays
    r >>= 3  # Keep top 5 bits
    g >>= 2  # Keep top 6 bits
    b >>= 3  # Keep top 5 bits

    # Combine into RGB 565 format
    rgb565 = (r << 11) | (g << 5) | b
    return rgb565.ravel()  # Convert the 2D array to a 1D array (raw data)

class DisplayManager:
    def __init__(self, fb_path="/dev/fb1", res=(240, 320),
                 font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size=24, bg_color=(255, 0, 0),
                 text_color=(255, 255, 255)):
        self.fb_path = fb_path
        self.res = res
        self.font = ImageFont.truetype(font_path, font_size)
        self.bg_color = bg_color
        self.text_color = text_color
        print(PIL.__version__)

    def draw_rotated_text(self, image, text, position, bg_color):
        """
        Draws rotated text onto an image.

        Args:
            image: PIL Image, The image object to draw on.
            text: str, The text to draw.
            position: tuple, The (x, y) position to draw the text.
            bg_color: tuple, The background color.

        Returns:
            PIL Image: The modified image with the rotated text.
        """
        # Draw text onto a separate image
        draw = ImageDraw.Draw(image)
        text_width, text_height = self.font.getsize_singleline(text)
        text_image = Image.new("RGB", (text_width, text_height), bg_color)
        text_draw = ImageDraw.Draw(text_image)
        text_draw.text((0, 0), text, font=self.font, fill=self.text_color)

        # Rotate the text image by 90 degrees
        rotated_text = text_image.rotate(90, expand=True)

        # Paste the rotated text onto the main image at the calculated x-position
        image.paste(
            rotated_text,
            (position[1], image.height - rotated_text.height - position[0])
        )

        return image

    # def draw_display(self, last_tags_and_ids, bg_color=None):
    #     """
    #     Creates and draws an image for the display based on the provided data.
    #
    #     Args:
    #         last_tags_and_ids: dict, Data to display.
    #         bg_color: tuple, optional, The background color. Default is set in constructor.
    #
    #     Returns:
    #         None
    #     """
    #     bg_color_to_use = bg_color or self.bg_color
    #
    #     # Draw the various pieces of data onto the image
    #     texts = [
    #         (last_tags_and_ids["employee_name"], 5, 0),
    #         (last_tags_and_ids["last_employee_tap"], 5, 30),
    #         (last_tags_and_ids["order_id"], 5, 60),
    #         (last_tags_and_ids["last_order_tap"], 5, 90),
    #         ("Total Count: " + str(last_tags_and_ids["units_employee"]), 5, 120),
    #         ("Order Count: " + str(last_tags_and_ids["units_order"]), 5, 150)
    #     ]
    #     for text, x, y in texts:
    #         image = self.draw_rotated_text(image, text, (x, y), bg_color_to_use)
    #
    #     # Convert the image to RGB565 format and write to framebuffer
    #     raw_data = image_to_rgb565(image)
    #     write_to_framebuffer(raw_data, self.fb_path)

    def draw_display(self, operation_taps, bg_color=None):
        """
        Creates and draws an image for the display based on the provided data.

        Args:
            last_tags_and_ids: dict, Data to display.
            bg_color: tuple, optional, The background color. Default is set in constructor.

        Returns:
            None
        """
        bg_color_to_use = bg_color or self.bg_color
        image = Image.new("RGB", self.res, bg_color_to_use)

        sorted_records = sorted(operation_taps["Records"], key=lambda x: x["Timestamp"], reverse=True)
        if len(sorted_records) != 0:
            # Get the most recent timestamp
            most_recent_timestamp = sorted_records[0]["Timestamp"]
        else:
            most_recent_timestamp = None
        # Draw the various pieces of data onto the image
        texts = [
            (get_current_time(), 5, 0),
            (f"Last Tap: {most_recent_timestamp}", 5, 30),
            (f"Total Operations: {len(operation_taps['Records'])}", 5, 60),
            (f"Total Units: {sum([record['UoM'] for record in operation_taps.get('Records')])}", 5, 90),
        ]
        for text, x, y in texts:
            image = self.draw_rotated_text(image, text, (x, y), bg_color_to_use)

        # Convert the image to RGB565 format and write to framebuffer
        raw_data = image_to_rgb565(image)
        write_to_framebuffer(raw_data, self.fb_path)