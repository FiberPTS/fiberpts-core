#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DISPLAY_ERROR_MESSAGE="panel-ilitek-ili9341.*SPI transfer failed|spi_master.*failed to transfer one message from queue|panel-ilitek-ili9341.*\*ERROR\* Failed to update display"

env_file="$SCRIPT_DIR/../../app/.env.shared"

source "$env_file"

exec 200>"$DISPLAY_FRAME_BUFFER_LOCK_PATH" # Open the lock file for writing and assign file descriptor 200

trap 'flock -u 200' EXIT # Trap EXIT signal to ensure lock release on script exit

# Define the max_new_errors threshold
error_count_threshold=$DISPLAY_ERROR_COUNT_THRESHOLD # Replace with your actual threshold
error_count=0

# Extract the timestamp of the most recent error message
last_error_timestamp=$(dmesg | grep -E "$DISPLAY_ERROR_MESSAGE" | tail -1 | grep -oP '\[\s*\K\d+\.\d+')

# Initialize the current timestamp and counter
if [ -z "$last_error_timestamp" ]; then
    last_error_timestamp=0
else
    initial_errors=$(dmesg | grep -c -E "$DISPLAY_ERROR_MESSAGE")
    error_count=$((initial_errors % error_count_threshold))
fi

# Start monitoring dmesg
dmesg --follow | while read line; do
    # Check if the message is an error message
    if echo "$line" | grep -q -E "$DISPLAY_ERROR_MESSAGE"; then
        # Extract the floating-point timestamp
        new_error_timestamp=$(echo "$line" | grep -oP '\[\s*\K\d+\.\d+')
        # Update the last timestamp and reset counter if the error is new
        if (( $(echo "$new_error_timestamp > $last_error_timestamp" | bc -l) )); then
            # Error counting logic
            ((error_count++))
            if [ "$error_count" -gt "$error_count_threshold" ]; then
                flock -x 200 # Wait until lock is acquired
                rmmod ili9341
                sleep 0.5
                modprobe ili9341
                sleep 0.5
                flock -u 200 # Release the lock
                error_count=0
            fi
        fi
    fi
done
