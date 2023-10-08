#!/bin/bash

echo "Script started."

# Define the base directory for the NFC tracking application.
BASE_DIR="/home/potato/FiberPTS/src/iot"

# Define the names and paths of the programs to be monitored.
PROGRAM_NAMES=(
    "nfc_tap_listener.c"
    "operation_tap_listener.c"
    "tap_event_handler.py"
)

echo "Defining program paths."
for idx in "${!PROGRAM_NAMES[@]}"; do
    PROGRAM_PATHS[$idx]="${BASE_DIR}/${PROGRAM_NAMES[$idx]}"
done

echo "Setting up SIGTERM handler."
# Kill the monitored programs when the script receives a SIGTERM signal.
on_sigterm() {
    echo "Received SIGTERM. Killing monitored programs."
    kill "$(cat /var/run/nfc_tap_listener.pid)"
    kill "$(cat /var/run/operation_tap_listener.pid)"
    kill "$(cat /var/run/tap_event_handler.pid)"
    exit 0
}

# Register the function to be called on SIGTERM
trap on_sigterm SIGTERM

# Function to check WiFi connection and reconnect if disconnected
check_wifi() {
    echo "Checking WiFi connection."
    # Check if "FERRARAMFG" is in the list of available WiFi networks
    if nmcli device wifi list | grep -q "FERRARAMFG"; then
        # Check if not already connected to "FERRARAMFG"
        if ! nmcli con show --active | grep -q "FERRARAMFG"; then
            echo "Connecting to FERRARAMFG."
            # Try to connect to "FERRARAMFG"
            nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
            # Ensure connection is up
            nmcli con up FERRARAMFG
        fi
    fi
}

# Extend the Python path to include a custom directory.
export PYTHONPATH=$PYTHONPATH:/home/potato/.local/lib/python3.9/site-packages

# Main loop to continuously monitor the programs.
while true; do
    # Check the WiFi connection.
    check_wifi

    echo "Checking if the programs are running."
    # Check if the first program is running.
    if pgrep -f "${PROGRAM_NAMES[0]}" > /dev/null; then
        STATUS_1="Online"
    else
        STATUS_1="Offline"
        echo "Starting the first program."
        # If not running, try to restart the program and log its output.
        "${PROGRAM_PATHS[0]}" >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/nfc_tap_listener.pid
    fi

    # Check if the second program is running.
    if pgrep -f "${PROGRAM_NAMES[1]}" > /dev/null; then
        STATUS_2="Online"
    else
        STATUS_2="Offline"
        echo "Starting the second program."
        # If not running, try to restart the program and log its output.
        "${PROGRAM_PATHS[1]}" >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/operation_tap_listener.pid
    fi

    # Check if the third program is running.
    if pgrep -f "${PROGRAM_PATHS[2]}" > /dev/null; then
        STATUS_3="Online"
    else
        STATUS_3="Offline"
        echo "Starting the third program."
        # If not running, try to restart the program and log its output.
        "${PROGRAM_PATHS[2]}" >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/tap_event_handler.pid
    fi

    echo "Checking overall status."
    # Determine the overall status of all programs.
    if [ "$STATUS_1" = "Offline" ] || [ "$STATUS_2" = "Offline" ] || [ "$STATUS_3" = "Offline" ]; then
        STATUS="Offline"
    else
        STATUS="Online"
    fi

    echo "Sleeping for 10 seconds."
    # Pause for 10 seconds before checking the programs again.
    sleep 10
done
