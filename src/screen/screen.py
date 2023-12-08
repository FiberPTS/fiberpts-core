from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

def image_to_rgb565(image):
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


def write_to_framebuffer(data, path="/dev/fb2"):
    try:
        with open(path, "wb") as f:
            f.write(data.tobytes())
    except IOError as e:
        print(f"Error writing to framebuffer: {e}")

def draw_text(image, text, position, text_color, font_path=None, font_size=24):
    # Create an ImageDraw object
    draw = ImageDraw.Draw(image)

    # Specify the font (default or provided)
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()

    # Draw the text
    draw.text(position, text, font=font, fill=text_color)

    return image

def draw_display(bg_color, text, text_position, text_color, res=(240, 320), font_path=None):
    # Create a new image with background color
    image = Image.new("RGB", res, bg_color)

    # Draw text on the image
    image = draw_text(image, text, text_position, text_color, font_path=font_path)

    # Convert the image to RGB565 format and write to framebuffer
    raw_data = image_to_rgb565(image)
    write_to_framebuffer(raw_data)

# Main Execution
draw_display("black", "Hello World!", (10, 10), "white", font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")