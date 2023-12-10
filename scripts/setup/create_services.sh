#!/bin/bash

# Directory containing service files
SERVICE_DIR="/opt/FiberPTS/services"

# Directory to store service files
SYSTEMD_DIR="/etc/systemd/system"

# Array to keep track of service filenames
service_filenames=()

# Copy loop: Iterate over each service file in the directory and copy them
for service_file in "$SERVICE_DIR"/*.service; do
    if [ -f "$service_file" ]; then
        # Copy the service file to the systemd directory
        cp "$service_file" "$SYSTEMD_DIR"

        # Extract just the filename for enabling later
        service_filenames+=("$(basename "$service_file")")

        echo "Service file copied: $(basename "$service_file")"
    else
        echo "No service files found in $SERVICE_DIR"
    fi
done

# Reload systemd to recognize new service files
systemctl daemon-reload

# Enable loop: Iterate over the copied service filenames and enable them
for service_filename in "${service_filenames[@]}"; do
    systemctl enable "$service_filename"
    echo "Service enabled: $service_filename"
done

echo "All service files are now copied, daemon reloaded, and services enabled."
