import csv
import datetime
from googleapiutils2 import Drive, GoogleMimeTypes
from google.oauth2.service_account import Credentials as ServiceCredentials
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# FILE_PATH = '/var/FiberPTS/data.csv'
FILE_PATH = "/Users/nxfer/Github Repositories/FiberPTS"
SERVICE_ACCOUNT_JSON_PATH = "/Users/nxfer/Github Repositories/FiberPTS/indigo-history-397015-bf31ea2c51a7.json"


def json_to_csv(json_data, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        fieldnames = ["Machine ID", "UoM", "Timestamp"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in json_data["Records"]:
            writer.writerow(record)


def upload_file_to_drive(file_paths, parent_folder_id="1xonItT9hqD0goUq2qfldvfFTOWyhRLcz"):
    # Load the service account credentials
    drive = Drive(creds=ServiceCredentials.from_service_account_file(SERVICE_ACCOUNT_JSON_PATH))

    # Check if today's folder exists
    name = datetime.datetime.now().strftime('%m-%d-%y')
    folders = drive.list(
        query=f"name='{name}' and '{parent_folder_id}' in parents and mimeType='{GoogleMimeTypes.folder.value}'")
    folder = next(folders, None)
    print(list(folders))

    # If the folder does not exist, create it
    if not folder:
        folder = drive.create(name=name, parents=[parent_folder_id], mime_type=GoogleMimeTypes.folder)

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

        print(f'File uploaded with ID: {uploaded_file["id"]}')


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
        'Machine ID': ['Machine1'] * num_records,
        'UoM': [1] * num_records,
        'Timestamp': timestamps
    })

    # Save to CSV
    df.to_csv(f"{FILE_PATH}/{filename}", index=False)

    return f"{FILE_PATH}/{filename}"


def generate_graph_from_csv(csv_path, image_path):
    # Read the CSV data
    data = pd.read_csv(csv_path)

    if data.empty:
        print("######## CSV IS EMPTY #########")
        return False

    data['Timestamp'] = pd.to_datetime(data['Timestamp'])

    # Sort by timestamp
    data = data.sort_values(by='Timestamp')

    # Compute the cumulative UoM
    data['Cumulative UoM'] = data['UoM'].cumsum()

    # Create the plot
    plt.figure(figsize=(10, 5))
    plt.plot(data['Timestamp'], data['Cumulative UoM'], marker='o')

    # Set the x-axis to represent every hour from 6am to 6pm
    start_time = data['Timestamp'].iloc[0].replace(hour=6, minute=0, second=0)
    end_time = data['Timestamp'].iloc[0].replace(hour=18, minute=0, second=0)
    hours = pd.date_range(start=start_time, end=end_time, freq='H')

    plt.gca().set_xticks(hours)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%I%p'))
    plt.gca().xaxis.set_minor_locator(mdates.HourLocator())

    plt.title('Cumulative UoM over Time')
    plt.xlabel('Timestamp')
    plt.ylabel('Cumulative UoM')
    plt.xticks(rotation=45)
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
    time_diffs = data['Timestamp'].diff().dropna()  # Time difference between consecutive rows
    avg_op_time = format_timedelta(time_diffs.mean())
    min_op_time = format_timedelta(time_diffs.min())
    max_op_time = format_timedelta(time_diffs.max())
    total_units = data['UoM'].sum()
    total_ops = len(data)

    return {
        'Average Operation Time': avg_op_time,
        'Minimum Operation Time': min_op_time,
        'Maximum Operation Time': max_op_time,
        'Total Units': total_units,
        'Total Operations': total_ops
    }


def generate_pdf_report(analytics, graph_path, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add analytics data
    for key, value in analytics.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

    # Add graph
    pdf.ln(10)
    pdf.image(graph_path, x=10, y=None, w=190)

    pdf.output(pdf_path)


def ready_to_upload():
    current_time = datetime.datetime.now(tz=datetime.timezone.utc).astimezone(
        datetime.timezone(datetime.timedelta(hours=-5)))  # Convert to EST
    return current_time.hour >= 18


def upload_report(data, folder_path):
    # if not ready_to_upload():
    #     return
    # csv_file = generate_sample_data("data.csv", num_records=100)
    csv_file_path = f"{folder_path}/data.csv"
    graph_file_path = f"{folder_path}/graph.png"
    report_file_path = f"{folder_path}/report.pdf"

    # Generate CSV file
    json_to_csv(data, csv_file_path)

    # Generate graph
    if not generate_graph_from_csv(csv_file_path, graph_file_path):
        return False

    # Compute analytics
    analytics = compute_analytics(csv_file_path)

    # Generate PDF report
    generate_pdf_report(analytics, graph_file_path, report_file_path)

    # Upload files
    files_to_upload = [csv_file_path, report_file_path]
    upload_file_to_drive(files_to_upload)
    return True