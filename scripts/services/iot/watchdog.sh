#!/bin/bash

# Define the base directory for the NFC tracking application.
BASE_DIR="/home/potato/NFC_Tracking"
# Define the names and paths of the programs to be monitored.
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
=======
# Specify the base directory
BASE_DIR="/home/potato/NFC_Tracking"

# Specify the name and path of your C programs
PROGRAM_NAME_1="read_ultralight"
PROGRAM_NAME_2="button_listener"
PROGRAM_NAME_3="screen.py"  # New program
PROGRAM_PATH_1="$BASE_DIR/$PROGRAM_NAME_1"
PROGRAM_PATH_2="$BASE_DIR/$PROGRAM_NAME_2"
PROGRAM_PATH_3="$BASE_DIR/$PROGRAM_NAME_3"

# Get the machine unique identifier (using /etc/machine-id as an example)
MACHINE_ID=$(cat /etc/machine-id)

# Function to handle SIGTERM signal
>>>>>>> 10f21de177edf1dd66fe2f3bb020e6649b7cdc26
on_sigterm() {
    kill $(cat /var/run/read_ultralight.pid)
    kill $(cat /var/run/button_listener.pid)
    kill $(cat /var/run/screen.pid)
    exit 0
}

<<<<<<< HEAD
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
=======
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
>>>>>>> 10f21de177edf1dd66fe2f3bb020e6649b7cdc26
    #    nmcli device wifi connect "iPhone (202)" password thehomiepass
    #    nmcli con up "iPhone (202)"
    #fi
}

<<<<<<< HEAD
# Extend the Python path to include a custom directory.
export PYTHONPATH=$PYTHONPATH:/home/potato/.local/lib/python3.9/site-packages

# Main loop to continuously monitor the programs.
while true; do
    # Check the WiFi connection.
    check_wifi

    # Check if the first program is running.
    if pgrep -f $PROGRAM_NAMES[0] > /dev/null
=======
export PYTHONPATH=$PYTHONPATH:/home/potato/.local/lib/python3.9/site-packages

while true; do
    check_wifi
    # Check if the programs are running
    if pgrep -f $PROGRAM_NAME_1 > /dev/null
>>>>>>> 10f21de177edf1dd66fe2f3bb020e6649b7cdc26
    then
        STATUS_1="Online"
    else
        STATUS_1="Offline"
<<<<<<< HEAD
        # If not running, try to restart the program and log its output.
        $PROGRAM_PATHS[0] >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/read_ultralight.pid
    fi

    # Check if the second program is running.
    if pgrep -f $PROGRAM_NAMES[2] > /dev/null
=======

        # Try to restart the program
        $PROGRAM_PATH_1 >> /var/log/programs.log 2>&1 &

        # Write the PID of the new program instance to the pidfile
        echo $! > /var/run/read_ultralight.pid
    fi

    if pgrep -f $PROGRAM_NAME_2 > /dev/null
>>>>>>> 10f21de177edf1dd66fe2f3bb020e6649b7cdc26
    then
        STATUS_2="Online"
    else
        STATUS_2="Offline"
<<<<<<< HEAD
        # If not running, try to restart the program and log its output.
        $PROGRAM_PATHS[1] >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/button_listener.pid
    fi

    # Check if the third program is running.
    if pgrep -f $PROGRAM_NAMES[2] > /dev/null
=======

        # Try to restart the program
        $PROGRAM_PATH_2 >> /var/log/programs.log 2>&1 &

        # Write the PID of the new program instance to the pidfile
        echo $! > /var/run/button_listener.pid
    fi
    
    if pgrep -f $PROGRAM_NAME_3 > /dev/null
>>>>>>> 10f21de177edf1dd66fe2f3bb020e6649b7cdc26
    then
        STATUS_3="Online"
    else
        STATUS_3="Offline"
<<<<<<< HEAD
        # If not running, try to restart the program and log its output.
        $PROGRAM_PATHS[2] >> /var/log/programs.log 2>&1 &
        # Store the PID of the restarted program.
        echo $! > /var/run/screen.pid
    fi

    # Determine the overall status of all programs.
=======

        # Try to restart the program
        $PROGRAM_PATH_3 >> /var/log/programs.log 2>&1 &

        # Write the PID of the new program instance to the pidfile
        echo $! > /var/run/screen.pid
    fi

    # Set overall status
>>>>>>> 10f21de177edf1dd66fe2f3bb020e6649b7cdc26
    if [ "$STATUS_1" = "Offline" ] || [ "$STATUS_2" = "Offline" ] || [ "$STATUS_3" = "Offline" ]
    then
        STATUS="Offline"
    else
        STATUS="Online"
    fi

<<<<<<< HEAD
    # Pause for 60 seconds before checking the programs again.
    sleep 60
done
=======
    # Wait for a while before checking again
    sleep 60
done
>>>>>>> 10f21de177edf1dd66fe2f3bb020e6649b7cdc26
