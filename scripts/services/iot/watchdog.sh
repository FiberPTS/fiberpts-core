#!/bin/bash

# Define the base directory for the NFC tracking application.
BASE_DIR="/home/potato/FiberPTS/src/iot"

# Define the names and paths of the programs to be monitored.
PROGRAM_NAMES=(
    "nfc_tap_listener"
    "operation_tap_listener"
    "tap_event_handler.py"
)

declare -A PROGRAM_PIDS

for program in "${PROGRAM_NAMES[@]}"; do
    PROGRAM_PIDS["$program"]="/var/run/${program%.py}.pid"

update_permissions() {
    for program in "${PROGRAM_NAMES[@]}"; do
        chmod +x "${BASE_DIR}/${program}"
    done
}

check_program() {
    local program=$1
    if pgrep -f "${program}" > /dev/null; then
        echo "Online"
    else
        echo "Offline"
        echo "Starting ${program}."
        "${BASE_DIR}/${program}" >> /var/log/programs.log 2>&1 &
        echo $! > "${PROGRAM_PIDS[${program}]}"
    fi
}

# Kill the monitored programs when the script receives a SIGTERM signal.
on_sigterm() {
    for pid_file in "${PROGRAM_PIDS[@]}"; do
        if [[ -f "${pid_file}" ]]; then
            kill "$(cat "${pid_file}")"
        fi
    done
    exit 0
}

# Register the function to be called on SIGTERM
trap on_sigterm SIGTERM

# Function to check WiFi connection and reconnect if disconnected
check_wifi() {
    # Check if "FERRARAMFG" is in the list of available WiFi networks
    if nmcli device wifi list | grep -q "FERRARAMFG"; then
        # Check if not already connected to "FERRARAMFG"
        if ! nmcli con show --active | grep -q "FERRARAMFG"; then
            # Try to connect to "FERRARAMFG"
            nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
            # Ensure connection is up
            nmcli con up FERRARAMFG
        fi
    fi
}

# Extend the Python path to include a custom directory.
export PYTHONPATH=$PYTHONPATH:/home/potato/.local/lib/python3.10/site-packages

# Update the program file permissions to be executable
update_permissions

# Main loop to continuously monitor the programs.
while true; do
    # Check the WiFi connection.
    check_wifi

    for program in "${PROGRAM_NAMES[@]}"; do
        check_program "${program}"
    done

    # Pause for 60 seconds before checking the programs again.
    sleep 10
done
