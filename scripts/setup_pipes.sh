#!/bin/bash

# Load the environment variables from the .env.shared file
set -a  # automatically export all variables
source /opt/FiberPTS/.env.shared
set +a  # stop automatically exporting

# Create the directory for pipes if it doesn't exist
mkdir -p "$PIPE_FOLDER_PATH"

# Create the FIFO pipes
mkfifo "$TOUCH_SENSOR_TO_SCREEN_PIPE"
echo "FIFO pipe $TOUCH_SENSOR_TO_SCREEN_PIPE created"

mkfifo "$NFC_TO_SCREEN_PIPE"
echo "FIFO pipe $NFC_TO_SCREEN_PIPE created"