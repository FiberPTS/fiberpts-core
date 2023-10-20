import csv
import datetime
from googleapiutils2 import Drive, GoogleMimeTypes
from google.oauth2.service_account import Credentials as ServiceCredentials
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from zoneinfo import ZoneInfo
import os


MACHINE_NAME = os.environ.get('MACHINE_NAME', 'Default')
FILE_PATH = "/Users/nxfer/Github Repositories/FiberPTS"
SERVICE_ACCOUNT_JSON_PATH = "/home/potato/FiberPTS/gdrive-api-key.json"


def json_to_csv(json_data, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        fieldnames = ["Device ID", "UoM", "Timestamp"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in json_data["Records"]:
            writer.writerow(record)


def upload_file_to_drive(file_paths, parent_folder_id="1xonItT9hqD0goUq2qfldvfFTOWyhRLcz"):
    try:
        # Load the service account credentials
        drive = Drive(creds=ServiceCredentials.from_service_account_file(SERVICE_ACCOUNT_JSON_PATH))

        # Get the current time in UTC
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        # Convert to Eastern Time
        now_est = now_utc.astimezone(ZoneInfo('America/New_York'))

        # Format 
        folder_name = now_est.strftime('%m-%d-%y')
        folders = drive.list(
            query=f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='{GoogleMimeTypes.folder.value}'")
        folder = next(folders, None)

        # If the folder does not exist, create it
        if not folder:
            folder = drive.create(name=folder_name, parents=[parent_folder_id], mime_type=GoogleMimeTypes.folder)

        for file_path in file_paths:
            file_name = file_path.split('/')[-1]

            # Check if the file already exists in the folder
            files = drive.list(query=f"name='{file_name}' and '{folder['id']}' in parents")
            existing_file = next(files, None)

            # Metadata for the file
            file_metadata = {
                'name': file_name,
                'parents': [folder["id"]]
            }

            # Get appropriate mime type
            mime_map = {
                'csv': GoogleMimeTypes.csv,
                'pdf': GoogleMimeTypes.pdf
            }
            mime_type = mime_map.get(file_name.split('.')[-1], GoogleMimeTypes.file)

            uploaded_file = drive.upload_file(
                filepath=file_path,
                name=file_metadata['name'],
                parents=[folder["id"]],
                body=file_metadata,
                update=False,
                mime_type=mime_type
            )

            if 'id' not in uploaded_file:
                print(f"Failed to upload file: {file_name}")
                return False

            print(f'File uploaded with ID: {uploaded_file["id"]}')

        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def generate_sample_data(filename, num_records=50):
    # Generate random timestamps within the 6am to 6pm period
    base_time = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = base_time + datetime.timedelta(hours=6)
    end_time = base_time + datetime.timedelta(hours=18)
    total_seconds = int((end_time - start_time).total_seconds())

    timestamps = [start_time + datetime.timedelta(seconds=np.random.randint(0, total_seconds)) for _ in
                  range(num_records)]
    timestamps.sort()  # Sort the timestamps

    # Create a DataFrame
    df = pd.DataFrame({
        'Device ID': ['Device1'] * num_records,
        'UoM': [1] * num_records,
        'Timestamp': timestamps
    })

    # Save to CSV
    df.to_csv(f"{FILE_PATH}/{filename}", index=False)

    return f"{FILE_PATH}/{filename}"

# TOOD: Review this and comment
def generate_average_delta_graph_from_csv(csv_path, image_path):
    # Read the CSV data
    data = pd.read_csv(csv_path)

    if data.empty:
        print("Data is empty!")
        return False

    print("Data is not empty!")

    data['Timestamp'] = pd.to_datetime(data['Timestamp'])
    data = data.sort_values(by='Timestamp')

    # Calculate the time deltas in seconds
    data['Time Delta'] = data['Timestamp'].diff().dt.total_seconds()

    # Shift the 'Time Delta' column up so that each time delta is associated with the first timestamp in each pair
    data['Time Delta'] = data['Time Delta'].shift(-1)

    # Initialize an empty list to store the hourly averages
    hourly_avg_list = []

    # Loop through each unique hour in the data
    for hour in pd.date_range(start=data['Timestamp'].min().replace(minute=0, second=0), end=data['Timestamp'].max(), freq='H'):
        end_time = hour + pd.Timedelta(hours=1)
        mask = (data['Timestamp'] >= hour) & (data['Timestamp'] < end_time)
        avg_delta = data.loc[mask, 'Time Delta'].mean()

        # Handle NaN values
        if pd.isna(avg_delta):
            continue
            # avg_delta = 0

        hourly_avg_list.append({'Timestamp': end_time, 'Hourly Avg Time Delta': avg_delta / 60})  # Convert to minutes

    # Convert the list of dictionaries to a DataFrame
    hourly_avg = pd.DataFrame(hourly_avg_list)
    if hourly_avg.empty:
        return False

    print("Average time deltas computed!")

    # Create the plot
    plt.figure(figsize=(10, 5))
    plt.plot(hourly_avg['Timestamp'], hourly_avg['Hourly Avg Time Delta'], marker='o', label='Hourly Avg Time Delta')

    # Get the current time in UTC
    today = datetime.datetime.now(datetime.timezone.utc).astimezone(ZoneInfo('America/New_York')).date()

    # Set the start time to 6 am
    start_time = datetime.datetime(today.year, today.month, today.day, 6, 0, 0)

    # Set the end time to 6 pm
    end_time = datetime.datetime(today.year, today.month, today.day, 23, 0, 0)
    hours = pd.date_range(start=start_time, end=end_time, freq='H')

    plt.gca().set_xticks(hours)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%I%p'))

    plt.title('Hourly Average Time Delta')
    plt.xlabel('Timestamp')
    plt.ylabel('Average Time Delta (minutes)')
    plt.xticks(rotation=45)
    plt.xlim(start_time, end_time)
    plt.grid(True, which='both', axis='x', linestyle='--')
    plt.legend()

    print("Plot created!")

    plt.tight_layout()

    # Save the plot as an image
    plt.savefig(image_path)
    plt.close()

    print(f"Image saved to {image_path}!")
    return True

def generate_graph_from_csv(csv_path, image_path):
    # Read the CSV data
    data = pd.read_csv(csv_path)

    if data.empty:
        return False

    data['Timestamp'] = pd.to_datetime(data['Timestamp'])

    # Sort by timestamp
    data = data.sort_values(by='Timestamp')

    # Compute the cumulative UoM
    data['Cumulative UoM'] = data['UoM'].cumsum()

    # Create the plot
    plt.figure(figsize=(10, 5))
    plt.plot(data['Timestamp'], data['Cumulative UoM'], marker='o')

    # Get the current time in UTC
    today = datetime.datetime.now(datetime.timezone.utc).astimezone(ZoneInfo('America/New_York')).date()

    # Set the start time to 6 am
    start_time = datetime.datetime(today.year, today.month, today.day, 6, 0, 0)

    # Set the end time to 6 pm
    end_time = datetime.datetime(today.year, today.month, today.day, 23, 0, 0)
    hours = pd.date_range(start=start_time, end=end_time, freq='H')

    plt.gca().set_xticks(hours)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%I%p'))

    plt.title('Cumulative UoM over Time')
    plt.xlabel('Timestamp')
    plt.ylabel('Cumulative UoM')
    plt.xticks(rotation=45)
    plt.xlim(start_time, end_time)
    plt.grid(True, which='both', axis='x', linestyle='--')

    plt.tight_layout()

    # Save the plot as an image
    plt.savefig(image_path)
    plt.close()
    return True


def format_timedelta(td):
    # Extract hours, minutes, and seconds from the timedelta
    total_seconds = td.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Return formatted string
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def compute_analytics(csv_path):
    data = pd.read_csv(csv_path)
    data['Timestamp'] = pd.to_datetime(data['Timestamp'])

    # Compute metrics
    time_diffs = data['Timestamp'].diff().dropna()
    if time_diffs.empty:
        avg_op_time = "N/A"
        min_op_time = "N/A"
        max_op_time = "N/A"
    else:
        avg_op_time = format_timedelta(time_diffs.mean())
        min_op_time = format_timedelta(time_diffs.min())
        max_op_time = format_timedelta(time_diffs.max())
    
    total_units = data['UoM'].sum()
    total_ops = len(data)

    return {
        'Average Action Tap Time': avg_op_time,
        'Minimum Action Tap Time': min_op_time,
        'Maximum Action Tap Time': max_op_time,
        'Total Units': total_units,
        'Total Action Taps': total_ops
    }


def generate_pdf_report(analytics, graph1_path, graph2_path, folder_path):
    pdf = FPDF()
    pdf.add_page()
    pdf_path = f"{folder_path}/{MACHINE_NAME}-Report.pdf"
    
    # Add title to the report
    pdf.set_font("Arial", size=14, style='B')
    title = ' '.join(MACHINE_NAME.split('-'))
    pdf.cell(0, 10, txt=f"{title} Report", ln=True, align='C')

    # Add analytics data
    pdf.set_font("Arial", size=12)
    for key, value in analytics.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

    # Add graph
    pdf.ln(10)
    pdf.image(graph1_path, x=10, y=None, w=190)

    # Add average delta graph
    pdf.ln(10)
    pdf.image(graph2_path, x=10, y=None, w=190)

    pdf.output(pdf_path)
    return pdf_path


def ready_to_upload(action_taps):
    if len(action_taps["Records"]) == 0:
        return False
    
    current_time = datetime.datetime.now(tz=datetime.timezone.utc).astimezone(
        datetime.timezone(datetime.timedelta(hours=-5)))  # Convert to EST
    return current_time.hour >= 19

def upload_report(data, folder_path):
    # if not ready_to_upload():
    #     return
    # csv_file = generate_sample_data("data.csv", num_records=100)
    csv_path = f"{folder_path}/{MACHINE_NAME}.csv"
    graph1_path = f"{folder_path}/{MACHINE_NAME}-graph-delta.png"
    graph2_path = f"{folder_path}/{MACHINE_NAME}-graph-avg-delta.png"

    # Generate CSV file
    json_to_csv(data, csv_path)

    # Generate graph
    if (not generate_graph_from_csv(csv_path, graph1_path) or 
        not generate_average_delta_graph_from_csv(csv_path, graph2_path)):
        return False

    # Compute analytics
    analytics = compute_analytics(csv_path)

    print("Analytics Computed!")

    # Generate PDF report
    pdf_path = generate_pdf_report(analytics, graph1_path, graph2_path, folder_path)

    print("PDF Report Generated!")

    # Upload files
    files_to_upload = [csv_path, pdf_path]
    upload_file_to_drive(files_to_upload)
    return True