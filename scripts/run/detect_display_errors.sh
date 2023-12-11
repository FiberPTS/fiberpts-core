#!/bin/bash

# Error message to look for
ERROR_PATTERN="TOBEDETERMINED"

while true; do
    # Check the dmesg output for the error pattern
    if dmesg | grep -q "$ERROR_PATTERN"; then
        echo "Error detected. Initiating reboot."
        # Use 'sudo' if the script is not running as root
        sudo reboot
    fi

    # Wait for a specified time interval before checking again
    sleep 2
done