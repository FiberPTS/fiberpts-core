#!/bin/bash

# Define the base directory for the NFC tracking application.
BASE_DIR="/home/potato/NFC_Tracking"

<<<<<<< HEAD
# Define the names and paths of the programs to be monitored.
=======
# Define the names and paths of the C programs to be monitored.
>>>>>>> 1d3226f (Fix unnecessary variable creation)
PROGRAM_NAMES=(
    "nfc_tap_listener.c"
    "operation_tap_listener.c"
    "screen.py"
)
for idx in ${!PROGRAM_NAMES[@]}; do
    PROGRAM_PATHS[$idx]=("{$BASE_DIR}/${PROGRAM_NAMES[$idx]}")

# Retrieve the unique identifier for the machine.
MACHINE_ID=$(cat /etc/machine-id)

# Define a function to handle the SIGTERM signal.
# This function will kill the monitored programs when the script receives a SIGTERM signal.
on_sigterm() {
    kill $(cat /var/run/read_ultralight.pid)
    kill $(cat /var/run/button_listener.pid)
    kill $(cat /var/run/screen.pid)
    exit 0
}

# Register the SIGTERM signal handler.
trap on_sigterm SIGTERM

# Define a function to check the WiFi connection and attempt to reconnect if disconnected.
check_wifi() {
    # Check if the device is connected to the "FERRARAMFG" network.
    if ! nmcli con show --active | grep -q "FERRARAMFG"; then
        # If not connected, attempt to reconnect.
        nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
        nmcli con up FERRARAMFG
    fi
    # Uncomment the following lines to check and connect to another network named "iPhone (202)".
    #if ! nmcli con show --active | grep -q "iPhone (202)"
    #then
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
    if pgrep -f $PROGRAM_NAMES[2] > /dev/null
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