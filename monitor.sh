#!/bin/bash

# Specify the base directory
BASE_DIR="/home/potato/NFC_Tracking"

# Specify the name and path of your C program
PROGRAM_NAME="read_ultralight"
PROGRAM_PATH="$BASE_DIR/$PROGRAM_NAME"

# Specify the webhook URL
WEBHOOK_URL="https://hooks.airtable.com/workflows/v1/genericWebhook/appZUSMwDABUaufib/wflNUJAmKHitljnxa/wtrg0Rj5KswYoaOcF"

# Get the machine unique identifier (using /etc/machine-id as an example)
MACHINE_ID=$(cat /etc/machine-id)

# Function to handle SIGTERM signal
on_sigterm() {
    kill $(cat /var/run/read_ultralight.pid)
    # Prepare the data
    JSON_DATA=$(jq -n \
                    --arg mid "$MACHINE_ID" \
                    --arg pn "$PROGRAM_NAME" \
                    --arg ps "Offline" \
                    --arg ping "Ping" \
                    '{machine_id: $mid, program_name: $pn, status: $ps, message: $ping}')

    # Send the data
    curl -X POST -H "Content-Type: application/json" -d "$JSON_DATA" $WEBHOOK_URL
    exit 0
}

# Register the function to be called on SIGTERM
trap on_sigterm SIGTERM

# Run the get_ip program
$BASE_DIR/get_ip &

while true; do
    # Check if the program is running
    if pgrep -f $PROGRAM_NAME > /dev/null
    then
        STATUS="Online"
    else
        STATUS="Offline"

        # Try to restart the program
        $PROGRAM_PATH >> /var/log/read_ultralight.log 2>&1 &

        # Write the PID of the new program instance to the pidfile
        echo $! > /var/run/read_ultralight.pid
    fi
    # Prepare the data
    JSON_DATA=$(jq -n \
              --arg mid "$MACHINE_ID" \
              --arg pn "$PROGRAM_NAME" \
              --arg ps "$STATUS" \
              --arg ping "Ping" \
              '{machine_id: $mid, program_name: $pn, status: $ps, message: $ping}')

    # Send the data
    curl -X POST -H "Content-Type: application/json" -d "$JSON_DATA" $WEBHOOK_URL

    # Wait for a while before checking again
    sleep 60
done
