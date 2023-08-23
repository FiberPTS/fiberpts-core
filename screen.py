#!/usr/bin/python3.9
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time
import requests
import json
import datetime
from zoneinfo import ZoneInfo
import sys
import os
import signal
import boto3
import configparser

def handle_sigterm(signum, frame):
    print_log("Received SIGTERM, ending program...")
    sys.exit(0)  # Exit the program

# Set timezone to EST
os.environ['TZ'] = 'EST5EDT'
time.tzset()

BATCH_FILE_PATH = "/var/lib/screen/batched_button_presses.json"
LAST_TAGS_AND_IDS_FILE_PATH = "/var/lib/screen/last_tags_and_ids.json"


def print_log(format_str, *args):
    """
    Logs messages with a timestamp.
    """
    current_time = datetime.datetime.now(ZoneInfo('US/Eastern'))
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

    if format_str.startswith('\n'):
        print(f"\n{timestamp}::screen.py::", end='')  # add newline before the timestamp
        format_str = format_str[1:]  # remove the first character
    else:
        print(f"{timestamp}::screen.py::", end='')

    print(format_str.format(*args))


def perror_log(format_str, *args):
    """
    Logs error messages with a timestamp.
    """
    current_time = datetime.datetime.now(ZoneInfo('US/Eastern'))
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp}::screen.py::{format_str.format(*args)}", file=sys.stderr)

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
            perror_log(f"Error {response.status_code}: {response.text}")
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

#def create_image(width, height, color):
#    return Image.new("BGR;16", (width, height), color)

def draw_rotated_text(image, text, font, position, text_color, bg_color):
    draw = ImageDraw.Draw(image)
    # Draw text onto a separate image
    text_width, text_height = draw.textsize(text, font=font)
    text_image = Image.new("RGB", (text_width, text_height), bg_color)
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((0, 0), text, font=font, fill=text_color)

    # Rotate the text image by 90 degrees
    rotated_text = text_image.rotate(90, expand=True)

    # Paste the rotated text onto the main image at the calculated x-position
    image.paste(rotated_text, (position[1], image.height - rotated_text.height - position[0]))
    return image

def convert_to_rgb565(image):
    b, g, r = image.split()
    r = np.array(r, dtype=np.uint16) >> 3
    g = np.array(g, dtype=np.uint16) >> 2
    b = np.array(b, dtype=np.uint16) >> 3
    return (r << 11) | (g << 5) | b

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

def reset_screen(buffer_size=153600, path="/dev/fb1"):
    """
    Resets the screen to zeros
    """
    zero_data = bytearray(buffer_size)
    with open(path, "wb") as f:
        f.write(zero_data)

def format_utc_to_est(date_str):
    """Converts a UTC datetime string to EST and formats it."""
    if date_str == "None":
        return ""
    date_str = date_str.replace('Z', '')
    # Adjust the format to match the given string
    date_utc = datetime.datetime.fromisoformat(date_str).astimezone(datetime.timezone.utc)
    date_est = date_utc.astimezone(ZoneInfo('America/New_York'))
    if date_est.astimezone(ZoneInfo('US/Eastern')).dst():
        date_est += datetime.timedelta(hours=1)
    return date_est.strftime('%Y-%m-%d %l:%M %p')

def send_sqs_message(machine_id, request_type, request_data, timestamp,
                     queue_url='https://sqs.us-east-1.amazonaws.com/279304726956/AWSQueue.fifo'):
    """
    Send a message to an SQS queue.

    Parameters:
    - machine_id (str): The machine ID.
    - request_type (str): The type of request.
    - request_data (str/dict): The data related to the request.
    - timestamp (str): The timestamp of the request.
    - queue_url (str, optional): The SQS queue URL. Default is the provided URL.

    Returns:
    - bool: True if the message was successfully sent, False otherwise.
    """

    # Initialize the SQS client
    sqs = boto3.client('sqs', region_name='us-east-1')

    if request_type == "button":
        request_data = json.dumps(request_data)

    # Create the message payload
    message_body = {
        "machine_id": machine_id,
        "request_type": request_type,
        "request_data": request_data,
        "timestamp": timestamp
    }

    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),  # Convert dict to string
            MessageGroupId=machine_id  # Only required for FIFO queues
        )

        # Print the message ID and MD5 (This can be adjusted based on whether you want to print or return this information.)
        print_log(f"MessageId: {response['MessageId']}")
        print_log(f"MD5: {response['MD5OfMessageBody']}")

        return True  # Message was successfully sent

    except botocore.exceptions.EndpointConnectionError as e:
        # Handle the exception and print/log an error message
        print_log(f"Error sending message to SQS: {e}")
        return False  # Failed to send the message

def create_image(width, height, bg_color):
    return Image.new("RGB", (width, height), bg_color)

def save_last_tags_and_ids_to_file(machine_record_id, employee_tag, employee_name, order_tag, order_id, last_employee_tap, last_order_tap, units_order, units_employee):
    """Save the last employee tag, employee name, order tag, order id, last employee tap, and last order tap to a file."""
    data = {
        "machine_record_id": machine_record_id,
        "last_employee_tag": employee_tag,
        "employee_name": employee_name,
        "last_order_tag": order_tag,
        "order_id": order_id,
        "last_employee_tap": last_employee_tap,
        "last_order_tap": last_order_tap,
        "units_order": units_order,
        "units_employee": units_employee
    }
    with open(LAST_TAGS_AND_IDS_FILE_PATH, 'w') as file:
        json.dump(data, file)

def load_last_tags_and_ids_from_file():
    """Load the last employee tag, employee name, order tag, order id, last employee tap, and last order tap from the file."""
    try:
        with open(LAST_TAGS_AND_IDS_FILE_PATH, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "last_employee_tag": "None",
            "employee_name": "No Employee",
            "last_order_tag": "None",
            "order_id": "No Order",
            "last_employee_tap": "Unknown",
            "last_order_tap": "Unknown",
            "units_order": 0,
            "units_employee": 0
        }

def save_batch_to_file(batch):
    """Save the current batched button presses to a file."""
    with open(BATCH_FILE_PATH, 'w') as file:
        json.dump(batch, file)

def load_batch_from_file():
    """Load the saved batched button presses from the file."""
    try:
        with open(BATCH_FILE_PATH, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"Records": []}

def main():
    # Load AWS credentials from file
    config = configparser.ConfigParser()
    config.read('/home/potato/NFC_Tracking/.aws/credentials.txt')

    aws_access_key_id = config.get('Credentials', 'aws_access_key_id')
    aws_secret_access_key = config.get('Credentials', 'aws_secret_access_key')
    boto3.setup_default_session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                                region_name='us-east-1')
    machine_id = get_machine_id()
    signal.signal(signal.SIGTERM, handle_sigterm)
    print_log("Starting Screen.py")
    print_log("Pulling Previous Data")

    # Load the last tags, ids, and taps from file
    last_tags_and_ids = load_last_tags_and_ids_from_file()
    machine_record_id = last_tags_and_ids.get("machine_record_id","None")
    last_employee_tag = last_tags_and_ids["last_employee_tag"]
    employee_name = last_tags_and_ids["employee_name"]
    last_order_tag = last_tags_and_ids["last_order_tag"]
    order_id = last_tags_and_ids["order_id"]
    last_employee_tap = last_tags_and_ids["last_employee_tap"]
    last_order_tap = last_tags_and_ids["last_order_tap"]
    units_order = last_tags_and_ids["units_order"]
    units_employee = last_tags_and_ids["units_employee"]
    if machine_record_id == "None":
        field_ids = [("fldZsM3YEVQqpJMFF", "record_id")]
        reader_dict = get_record("appZUSMwDABUaufib", "tblFOfDowcZNlPRDL", field_ids, "fldbh9aMmA6qAoNKq", machine_id)
        if reader_dict:
            machine_record_id = reader_dict["record_id"]
    # Load the batched button presses from file
    button_presses = load_batch_from_file()

    fifo_path = "/tmp/screenPipe"
    # Load a font
    text_color = (255, 255, 255)
    bg_color = (255, 0, 0)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    res = (240, 320)
    fail = False
    batch_count = 5
    current_count = len(button_presses["Records"])  # Update current count based on the loaded batch
    print_log("Starting Display")
    try:
        while True:
            # Create an image and draw rotated text onto it
            image = create_image(res[0], res[1], bg_color)

            image = draw_rotated_text(image, employee_name, font, (5, 0), text_color, bg_color)
            image = draw_rotated_text(image, last_employee_tap, font, (5, 30), text_color, bg_color)

            image = draw_rotated_text(image, order_id, font, (5, 60), text_color, bg_color)
            image = draw_rotated_text(image, last_order_tap, font, (5, 90), text_color, bg_color)

            image = draw_rotated_text(image, f"Total Count: {units_employee}", font, (5, 120), text_color, bg_color)

            image = draw_rotated_text(image, f"Order Count: {units_order}", font, (5, 150), text_color, bg_color)

            # Convert the image to RGB565 format and write to framebuffer
            raw_data = image_to_rgb565(image)
            write_to_framebuffer(raw_data)
            time.sleep(0.5)
            with open(fifo_path, "r") as fifo:
                data = fifo.read()
                if data:
                    data = data.split("-program-")
                    # Get current UTC time
                    now_utc = datetime.datetime.now(datetime.timezone.utc)
                    # Convert to Eastern Time Zone
                    now_est = now_utc.astimezone(ZoneInfo('US/Eastern'))
                    # Format the time to desired format: date, time, AM/PM
                    formatted_time = now_est.strftime('%Y-%m-%d %l:%M %p')
                    formatted_time_sec = now_est.strftime('%Y-%m-%d %l:%M:%S %p')
                    if data[0] == "read_ultralight.c":
                        if data[1][:-1] == "Failed":
                            fail = True
                        else:
                            tagId = data[1][:-1].lower()
                            field_ids = [("fldSrxknmVrsETFPx","order_id"), ("fldRi8wjAdfBkDhH8","record_id")]
                            order_dict = get_record("appZUSMwDABUaufib", "tbl6vse0gHkuPxBaT", field_ids, "fldRHuoXAQr4BF83j", tagId)
                            # When an employee tag is registered, the session unit counting is reset
                            if order_dict: # Order tag is registered
                                if tagId != last_order_tag:
                                    if send_sqs_message(machine_id, "order", tagId, formatted_time_sec):
                                        last_order_tag = tagId
                                        last_order_tap = formatted_time
                                        units_order = 0
                                        order_id = order_dict["order_id"][0]
                                    else:
                                        fail = True
                            else: # Unregistered tag treated as employee tag or employee tag is registered
                                if tagId != last_employee_tag:
                                    if send_sqs_message(machine_id, "employee", tagId, formatted_time_sec):
                                        last_employee_tag = tagId
                                        last_employee_tap = formatted_time
                                        units_order = 0
                                        units_employee = 0
                                        field_ids = [("fldOYvm4LsaM9pJNw", "employee_name"),("fld49C1CkqgW9hA3p","record_id")]
                                        employee_dict = get_record("appZUSMwDABUaufib", "tblbRYLt6rr4nTbP6", field_ids,
                                                                   "fldyYKc2g0dBdolKQ", tagId)
                                        if employee_dict:
                                            if employee_dict["employee_name"] == "None":
                                                employee_name = tagId
                                                # NEED TO CREATE EMPLOYEE TAG RECORD SO RECORD ID ISNT NONE
                                            else:
                                                employee_name = employee_dict["employee_name"][0]
                                        else:
                                            employee_name = tagId
                                    else:
                                        fail = True
                    else: # Button tap increases unit count
                        if last_employee_tag != "None" and last_order_tag != "None":
                            print_log("button pressed")
                            button_presses["Records"].append({"employee_tag": last_employee_tag, "order_tag": last_order_tag, "timestamp": formatted_time_sec})
                            current_count += 1
                            if current_count >= batch_count:
                                if send_sqs_message(machine_id, "button", button_presses, formatted_time_sec):
                                    current_count = 0
                                    button_presses = {"Records": []}
                                else:
                                    fail = True
                            units_order += 1
                            units_employee += 1
                        else:
                            fail = True
                        save_batch_to_file(button_presses)
                    save_last_tags_and_ids_to_file(machine_record_id, last_employee_tag, employee_name, last_order_tag, order_id, last_employee_tap, last_order_tap, units_order, units_employee)
                    temp_color = (0,170,0)
                    if fail:
                        temp_color = (0,0,255)
                        fail = False
                    # Handle the data, for example, draw on the LCD screen
                    # Create an image and draw rotated text onto it
                    image = create_image(res[0], res[1], temp_color)

                    image = draw_rotated_text(image, employee_name, font, (5, 0), text_color, temp_color)
                    image = draw_rotated_text(image, last_employee_tap, font, (5, 30), text_color, temp_color)

                    image = draw_rotated_text(image, order_id, font, (5, 60), text_color, temp_color)
                    image = draw_rotated_text(image, last_order_tap, font, (5, 90), text_color, temp_color)

                    image = draw_rotated_text(image, f"Total Count: {units_employee}", font, (5, 120), text_color, temp_color)

                    image = draw_rotated_text(image, f"Order Count: {units_order}", font, (5, 150), text_color, temp_color)

                    # Convert the image to RGB565 format and write to framebuffer
                    raw_data = image_to_rgb565(image)
                    write_to_framebuffer(raw_data)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print_log("Program Interrupted")

if __name__ == "__main__":
    main()