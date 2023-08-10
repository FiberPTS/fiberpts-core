from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time
import requests
import json

def get_machine_id():
    machine_id = None
    try:
        with open("/etc/machine-id", "r") as f:
            machine_id = f.read().strip()
    except FileNotFoundError:
        # If /etc/machine-id doesn't exist, you can also check /var/lib/dbus/machine-id
        try:
            with open("/var/lib/dbus/machine-id", "r") as f:
                machine_id = f.read().strip()
        except FileNotFoundError:
            return None
    return machine_id

def get_record(base_id, table_id, field_ids, filter_id, filter_value, api_key="patAQ8FpGw4j3oKk2.5f0606ba0571c34a403bdd282a25681187c1ac5f37050cca35a880e4def1a5ee"):
    URL = f"https://api.airtable.com/v0/{base_id}/{table_id}?returnFieldsByFieldId=true"

    HEADERS = {
        "Authorization": f"Bearer {api_key}",
        "Content-type": "application/json"
    }

    all_records = []
    offset = None

    # Pagination loop
    while True:
        if offset:
            paginated_url = f"{URL}&offset={offset}"
        else:
            paginated_url = URL

        response = requests.get(paginated_url, headers=HEADERS)
        data = json.loads(response.text)

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break

        all_records.extend(data.get("records", []))

        # Check if there's an offset for the next set of records
        offset = data.get("offset")
        if not offset:
            break

    # Filter records
    filtered_records = []
    for record in all_records:
        fields = record.get("fields", {})
        if fields.get(filter_id) == filter_value:
            filtered_records.append(fields)

    reader_data = {}
    if filtered_records:
        for field_id, name in field_ids:
            reader_data[name] = filtered_records[0].get(field_id, "None")

    return reader_data

def create_image(width, height, color):
    return Image.new("RGB", (width, height), color)

def draw_rotated_text(image, text, font, position):
    draw = ImageDraw.Draw(image)
    # Draw text onto a separate image
    text_width, text_height = draw.textsize(text, font=font)
    text_image = Image.new("RGB", (text_width, text_height), "white")
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((0, 0), text, font=font, fill="black")

    # Rotate the text image by 90 degrees
    rotated_text = text_image.rotate(90, expand=True)

    # Paste the rotated text onto the main image at the calculated x-position
    image.paste(rotated_text, (position[1], image.height - rotated_text.height - position[0]))
    return image

def convert_to_rgb565(image):
    r, g, b = image.split()
    r = np.array(r, dtype=np.uint16) >> 3
    g = np.array(g, dtype=np.uint16) >> 2
    b = np.array(b, dtype=np.uint16) >> 3
    return (r << 11) | (g << 5) | b

def write_to_framebuffer(data, path="/dev/fb1"):
    with open(path, "wb") as f:
        f.write(data.tobytes())

def reset_screen_image(res, color="white"):
    """
    Resets the screen to a solid color.

    Parameters:
    - width (int): Width of the screen.
    - height (int): Height of the screen.
    - color (str, optional): Color to set the screen to. Defaults to "white".
    """
    image = create_image(res[0], res[1], color)
    raw_data = convert_to_rgb565(image)
    write_to_framebuffer(raw_data)

def main():
    field_ids = [("fldJQd3TmtxURsQy0","employee_name"),("fldcFVtGOWbd8RgT6","order_id"), ("fld0prkx6YJPRJ8iO", "current_order_count"), ("fld4e2qIMLdMyTuLi", "total_count"), ("fldcaeaey2E5R8Iqp","last_order_tap"), ("fldVALQ4NGPNVrvZz","last_employee_tap")]
    record_dict = get_record("appZUSMwDABUaufib", "tblFOfDowcZNlPRDL", field_ids, "fldbh9aMmA6qAoNKq", get_machine_id())
    employee_name = record_dict["employee_name"]
    order_id = record_dict["order_id"]
    last_order_tap = record_dict["last_order_tap"]
    last_employee_tap = record_dict["last_employee_tap"]
    units_order = record_dict["current_order_count"]
    units_employee = record_dict["total_count"]
    fifo_path = "/tmp/screenPipe"
    # Load a font
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    res = (240, 320)
    flip = 1
    while True:
        with open(fifo_path, "r") as fifo:
            data = fifo.read()
            if data:
                data = data.split("-program-")
                if data[0] == "read_ultralight.c":
                    if data[1] == "Failed":
                        print(Failed)
                    else:
                        tagId = data[1][:-1].lower()
                        field_ids = [("fldOYvm4LsaM9pJNw","employee_name")]
                        employee_dict = get_record("appZUSMwDABUaufib", "tblbRYLt6rr4nTbP6", field_ids, "fldyYKc2g0dBdolKQ", tagId)
                        field_ids = [("fldSrxknmVrsETFPx","order_id")]
                        order_dict = get_record("appZUSMwDABUaufib", "tbl6vse0gHkuPxBaT", field_ids, "fldRHuoXAQr4BF83j", tagId)
                        # When an employee tag is registered, the session unit counting is reset
                        if order_dict: # Order tag is registered
                            units_order = 0
                            order_id = order_dict["order_id"]
                            last_order_tap = 0
                        else: # Unregistered tag treated as employee tag or employee tag is registered
                            if employee_dict:
                                employee_name = employee_dict["employee_name"]
                            last_employee_tap = 0
                            units_order = 0
                            units_employee = 0
                else: # Button tap increases unit count
                    units_order += 1
                    units_employee += 1
                data = data[1][:-1]
                # Handle the data, for example, draw on the LCD screen

                # Create an image and draw rotated text onto it
                image = create_image(res[0], res[1], "white")
                image = draw_rotated_text(image, f"{data}", font, (10, 0))

                # Convert the image to RGB565 format and write to framebuffer
                raw_data = convert_to_rgb565(image)
                write_to_framebuffer(raw_data)

                time.sleep(2)

                reset_screen_image(res)
        # Create an image and draw rotated text onto it
        image = create_image(res[0], res[1], "white")

        image = draw_rotated_text(image, f"Total Units: {units_employee}", font, (10, 0))

        image = draw_rotated_text(image, f"Session Units: {units_order}", font, (10, 30))

        # Convert the image to RGB565 format and write to framebuffer
        raw_data = convert_to_rgb565(image)
        write_to_framebuffer(raw_data)

if __name__ == "__main__":
    main()
