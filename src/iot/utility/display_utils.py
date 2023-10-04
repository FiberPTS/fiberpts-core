from PIL import Image, ImageDraw, ImageFont
import numpy as np

# TODO: Fix logging (program_name)
# TODO: Find and remove libraries that are unnecessary

class DisplayManager:
    def __init__(self, fb_path="/dev/fb1", res=(240, 320), font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size=24, bg_color=(255, 0, 0), text_color=(255, 255, 255)):
        self.fb_path = fb_path
        self.res = res
        self.font = ImageFont.truetype(font_path, font_size)
        self.bg_color = bg_color
        self.text_color = text_color

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
        text_width, text_height = draw.textsize(text, font=self.font)
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

    def image_to_rgb565(self, image):
        """
        Converts a PIL Image to RGB565 format.

        Args:
            image: PIL Image, The image object.

        Returns:
            np.array: The image data in RGB565 format.
        """
        # Split into R, G, B channels
        r, g, b = image.split()
    
        # Convert each channel to an appropriate numpy array
        r = np.array(r, dtype=np.uint16)
        g = np.array(g, dtype=np.uint16)
        b = np.array(b, dtype=np.uint16)
    
        # Right shift to fit into 565 format
        r >>= 3  # Keep top 5 bits
        g >>= 2  # Keep top 6 bits
        b >>= 3  # Keep top 5 bits
    
        # Combine into RGB 565 format
        rgb565 = (r << 11) | (g << 5) | b
    
        # Convert the 2D array to a 1D array (raw data)
        raw_data = rgb565.ravel()
    
        return raw_data

    def write_to_framebuffer(self, data):
        """
        Writes data to the framebuffer device.

        Args:
            data: np.array, The data to write.

        Returns:
            None
        """
        with open(self.fb_path, "wb") as f:
            f.write(data.tobytes())

    def draw_display(self, last_tags_and_ids, bg_color=None):
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
    
        image = draw_rotated_text(
            image, 
            last_tags_and_ids["employee_name"], 
            (5, 0), 
            bg_color_to_use
        )
        
        image = draw_rotated_text(
            image, 
            last_tags_and_ids["last_employee_tap"], 
            (5, 30), 
            bg_color_to_use
        )
        
        image = draw_rotated_text(
            image,
            last_tags_and_ids["order_id"],
            (5, 60),
            bg_color_to_use
        )
        
        image = draw_rotated_text(
            image,
            last_tags_and_ids["last_order_tap"],
            (5, 90),
            bg_color_to_use
        )
        
        image = draw_rotated_text(
            image,
            "Total Count: " + str(last_tags_and_ids["units_employee"]),
            (5, 120),
            bg_color_to_use
        )
        
        image = draw_rotated_text(
            image,
            "Order Count: " + str(last_tags_and_ids["units_order"]),
            (5, 150),
            bg_color_to_use
        )
    
        # Convert the image to RGB565 format and write to framebuffer
        raw_data = image_to_rgb565(image)
        write_to_framebuffer(raw_data)