#!/bin/bash

# Specify the base directory
BASE_DIR="/home/potato/NFC_Tracking"

# Specify the name and path of your C programs
PROGRAM_NAME_1="read_ultralight"
PROGRAM_NAME_2="button_listener"
PROGRAM_NAME_3="get_ip"
PROGRAM_NAME_4="screen.py"  # New program
PROGRAM_PATH_1="$BASE_DIR/$PROGRAM_NAME_1"
PROGRAM_PATH_2="$BASE_DIR/$PROGRAM_NAME_2"
PROGRAM_PATH_3="$BASE_DIR/$PROGRAM_NAME_3"
PROGRAM_PATH_4="$BASE_DIR/$PROGRAM_NAME_4"

# Get the machine unique identifier (using /etc/machine-id as an example)
MACHINE_ID=$(cat /etc/machine-id)

# Function to handle SIGTERM signal
on_sigterm() {
    kill $(cat /var/run/read_ultralight.pid)
    kill $(cat /var/run/button_listener.pid)
    kill $(cat /var/run/get_ip.pid)
    kill $(cat /var/run/screen.pid)
    exit 0
}

# Register the function to be called on SIGTERM
trap on_sigterm SIGTERM

# Function to check WiFi connection and reconnect if disconnected
check_wifi() {
    # Check if connected to "FERRARAMFG"
    #if ! nmcli con show --active | grep -q "FERRARAMFG"; then
    #	nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
    #    # If not connected, try to reconnect
    #    nmcli con up FERRARAMFG
    #fi
    local_ip = $(hostname -I | awk "{print $1}")
    echo "$local_ip" | nc -u -wl -b 255.255.255.255 12345
    if ! nmcli con show --active | grep -q "iPhone (202)"; then
        nmcli device wifi connect "iPhone (202)" password thehomiepass
        #nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
        # If not connected, try to reconnect
        #nmcli con up FERRARAMFG
    fi
}

while true; do
    check_wifi
    # Check if the programs are running
    if pgrep -f $PROGRAM_NAME_1 > /dev/null
    then
        STATUS_1="Online"
    else
        STATUS_1="Offline"

        # Try to restart the program
        $PROGRAM_PATH_1 >> /var/log/programs.log 2>&1 &

        # Write the PID of the new program instance to the pidfile
        echo $! > /var/run/read_ultralight.pid
    fi

    if pgrep -f $PROGRAM_NAME_2 > /dev/null
    then
        STATUS_2="Online"
    else
        STATUS_2="Offline"

        # Try to restart the program
        $PROGRAM_PATH_2 >> /var/log/programs.log 2>&1 &

        # Write the PID of the new program instance to the pidfile
        echo $! > /var/run/button_listener.pid
    fi
    
    if pgrep -f $PROGRAM_NAME_3 > /dev/null
    then
        STATUS_3="Online"
    else
        STATUS_3="Offline"

        # Try to restart the program
        $PROGRAM_PATH_3 >> /var/log/programs.log 2>&1 &

        # Write the PID of the new program instance to the pidfile
        echo $! > /var/run/get_ip.pid
    fi

    if pgrep -f $PROGRAM_NAME_4 > /dev/null
    then
        STATUS_4="Online"
    else
        STATUS_4="Offline"
        # Try to restart the program
        $PROGRAM_PATH_4 >> /var/log/programs.log 2>&1 &
        # Write the PID of the new program instance to the pidfile
        echo $! > /var/run/screen.pid
    fi

    # Set overall status
    if [ "$STATUS_1" = "Offline" ] || [ "$STATUS_2" = "Offline" ] || [ "$STATUS_4" = "Offline" ]
    then
        STATUS="Offline"
    else
        STATUS="Online"
    fi

    # Wait for a while before checking again
    sleep 60
done
