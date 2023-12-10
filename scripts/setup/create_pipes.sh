#!/bin/bash

# Create the directory for pipes if it doesn't exist
mkdir -p "$PIPE_FOLDER_PATH"

# Create the FIFO pipes
mkfifo "$TOUCH_SENSOR_TO_SCREEN_PIPE"
echo "FIFO pipe $TOUCH_SENSOR_TO_SCREEN_PIPE created"

mkfifo "$NFC_TO_SCREEN_PIPE"
echo "FIFO pipe $NFC_TO_SCREEN_PIPE created"