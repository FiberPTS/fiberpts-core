#!/bin/bash

# Define the base directory for the NFC tracking application.
BASE_DIR="/home/potato/NFC_Tracking"
# Define the names and paths of the programs to be monitored.
PROGRAM_NAMES=(
    "nfc_tap_listener.c"
    "operation_tap_listener.c"
    "display_and_data_handler.py"
)
for idx in ${!PROGRAM_NAMES[@]}; do
    PROGRAM_PATHS[$idx]=("{$BASE_DIR}/${PROGRAM_NAMES[$idx]}")

# Retrieve the unique identifier for the machine.
MACHINE_ID=$(cat /etc/machine-id)

# Kill the monitored programs when the script receives a SIGTERM signal.
on_sigterm() {
    kill $(cat /var/run/read_ultralight.pid)
    kill $(cat /var/run/button_listener.pid)
    kill $(cat /var/run/screen.pid)
    exit 0
}

# Register the function to be called on SIGTERM
trap on_sigterm SIGTERM

# Function to check WiFi connection and reconnect if disconnected
check_wifi() {
    # Check if connected to "FERRARAMFG"
    if ! nmcli con show --active | grep -q "FERRARAMFG"; then
    	nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
        # If not connected, try to reconnect
        nmcli con up FERRARAMFG
    fi
    #if ! nmcli con show --active | grep -q "iPhone (202)"; then
    #    nmcli device wifi connect "iPhone (202)" password thehomiepass
    #    nmcli con up "iPhone (202)"
    #fi
}

# Extend the Python path to include a custom directory.
export PYTHONPATH=$PYTHONPATH:/home/potato/.local/lib/python3.9/site-packages

# Main loop to continuously monitor the programs.
while true; do
    # Check the WiFi connection.
    check_wifi

    # Check if the first program is running.
    if pgrep -f $PROGRAM_NAMES[0] > /dev/null
    then
        STATUS_1="Online"
    else
        STATUS_1="Offline"
        # If not running, try to restart the program and log its output.
        $PROGRAM_PATHS[0] >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/read_ultralight.pid
    fi

    # Check if the second program is running.
    if pgrep -f $PROGRAM_NAMES[1] > /dev/null
    then
        STATUS_2="Online"
    else
        STATUS_2="Offline"
        # If not running, try to restart the program and log its output.
        $PROGRAM_PATHS[1] >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/button_listener.pid
    fi

    # Check if the third program is running.
    if pgrep -f $PROGRAM_NAMES[2] > /dev/null
    then
        STATUS_3="Online"
    else
        STATUS_3="Offline"
        # If not running, try to restart the program and log its output.
        $PROGRAM_PATHS[2] >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/screen.pid
    fi

    # Determine the overall status of all programs.
    if [ "$STATUS_1" = "Offline" ] || [ "$STATUS_2" = "Offline" ] || [ "$STATUS_3" = "Offline" ]
    then
        STATUS="Offline"
    else
        STATUS="Online"
    fi

    # Pause for 60 seconds before checking the programs again.
    sleep 60
done
