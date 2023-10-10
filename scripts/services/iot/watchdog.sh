#!/bin/bash

echo "Script started."

# Define the base directory for the NFC tracking application.
BASE_DIR="/home/potato/FiberPTS/src/iot"
echo "BASE_DIR set to: $BASE_DIR"

# Define the names and paths of the programs to be monitored.
PROGRAM_NAMES=(
    "nfc_tap_listener"
    "action_tap_listener"
    "tap_event_handler.py"
)
echo "PROGRAM_NAMES defined as: ${PROGRAM_NAMES[*]}"

declare -A PROGRAM_PIDS
echo "PROGRAM_PIDS array declared."

for program in "${PROGRAM_NAMES[@]}"; do
    PROGRAM_PIDS["$program"]="/var/run/${program%.py}.pid"
done
echo "PROGRAM_PIDS populated."

update_permissions() {
    echo "Entering update_permissions function."
    for program in "${PROGRAM_NAMES[@]}"; do
        chmod +x "${BASE_DIR}/${program}"
        echo "Permissions updated for: ${BASE_DIR}/${program}"
    done
    echo "Exiting update_permissions function."
}

check_program() {
    local program=$1
    echo "Checking program: $program"
    local pid=$(pgrep -f "${program}")
    if [[ $pid ]]; then
        echo "$program is Online."
        echo $pid > "${PROGRAM_PIDS[${program}]}"
    else
        echo "$program is Offline."
        echo "Starting ${program}."
        sudo "${BASE_DIR}/${program}" >> /var/log/programs.log 2>&1 &
        echo $! > "${PROGRAM_PIDS[${program}]}"
        echo "$program started with PID: $!"
    fi
}


# Kill the monitored programs when the script receives a SIGTERM or SIGINT (control+c) signal.
on_sigterm() {
    echo "Received SIGTERM or SIGINT. Shutting down monitored programs."
    for pid_file in "${PROGRAM_PIDS[@]}"; do
        if [[ -f "${pid_file}" ]]; then
            sudo kill "$(cat "${pid_file}")"
            echo "Killed program with PID from file: ${pid_file}"
        fi
    done
    exit 0
}

# Register the function to be called on SIGTERM
trap on_sigterm SIGTERM SIGINT
echo "Signal trap set for SIGTERM and SIGINT."

# Function to check WiFi connection and reconnect if disconnected
check_wifi() {
    echo "Checking WiFi connection."
    if nmcli device wifi list | grep -q "FERRARAMFG"; then
        if ! nmcli con show --active | grep -q "FERRARAMFG"; then
            echo "Connecting to FERRARAMFG."
            nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
            nmcli con up FERRARAMFG
        else
            echo "Already connected to FERRARAMFG."
        fi
    else
        echo "FERRARAMFG not found in the list of available WiFi networks."
    fi
}

# Extend the Python path to include a custom directory.
export PYTHONPATH=$PYTHONPATH:/home/potato/.local/lib/python3.10/site-packages
echo "PYTHONPATH extended."

# Update the program file permissions to be executable
update_permissions

# Main loop to continuously monitor the programs.
echo "Entering main loop."
while true; do
    check_wifi
    for program in "${PROGRAM_NAMES[@]}"; do
        check_program "${program}"
    done
    echo "Sleeping for 10 seconds."
    sleep 10
done
