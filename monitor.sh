#!/bin/bash

# Specify the base directory
BASE_DIR="/home/potato/NFC_Tracking"

# Specify the name and path of your C programs
PROGRAM_NAME_1="read_ultralight"
PROGRAM_NAME_2="button_listener"
PROGRAM_NAME_3="get_ip"
PROGRAM_PATH_1="$BASE_DIR/$PROGRAM_NAME_1"
PROGRAM_PATH_2="$BASE_DIR/$PROGRAM_NAME_2"
PROGRAM_PATH_3="$BASE_DIR/$PROGRAM_NAME_3"

# Specify the webhook URL
WEBHOOK_URL="https://hooks.airtable.com/workflows/v1/genericWebhook/appZUSMwDABUaufib/wflNUJAmKHitljnxa/wtrg0Rj5KswYoaOcF"

# Get the machine unique identifier (using /etc/machine-id as an example)
MACHINE_ID=$(cat /etc/machine-id)

# Function to handle SIGTERM signal
on_sigterm() {
    kill $(cat /var/run/read_ultralight.pid)
    kill $(cat /var/run/button_listener.pid)
    kill $(cat /var/run/get_ip.pid)
    # Prepare the data
    JSON_DATA=$(jq -n \
                    --arg mid "$MACHINE_ID" \
                    --arg ps "Offline" \
                    --arg ping "Ping" \
                    '{machine_id: $mid, status: $ps, message: $ping}')

    # Send the data
    curl -X POST -H "Content-Type: application/json" -d "$JSON_DATA" $WEBHOOK_URL
    exit 0
}

# Register the function to be called on SIGTERM
trap on_sigterm SIGTERM

# Function to check WiFi connection and reconnect if disconnected
check_wifi() {
    # Check if connected to "FERRARAMFG"
    if ! nmcli con show --active | grep -q "FERRARAMFG"; then
        # If not connected, try to reconnect
        nmcli con up FERRARAMFG
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

    # Set overall status
    if [ "$STATUS_1" = "Offline" ] || [ "$STATUS_2" = "Offline" ]
    then
        STATUS="Offline"
    else
        STATUS="Online"
    fi

    # Prepare the data
    JSON_DATA=$(jq -n \
                    --arg mid "$MACHINE_ID" \
                    --arg ps "$STATUS" \
                    --arg ping "Ping" \
                    '{machine_id: $mid, status: $ps, message: $ping}')
    # Send the data
    curl -X POST -H "Content-Type: application/json" -d "$JSON_DATA" $WEBHOOK_URL

    # Wait for a while before checking again
    sleep 60
done
