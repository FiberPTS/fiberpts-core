#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "$PIPE_FOLDER_PATH" ] || [ -z "$TOUCH_SENSOR_TO_SCREEN_PIPE" ] || [ -z "$NFC_TO_SCREEN_PIPE" ]; then
        echo "Required environment variables PIPE_FOLDER_PATH, TOUCH_SENSOR_TO_SCREEN_PIPE, or NFC_TO_SCREEN_PIPE are not set."
        exit 1
    fi
}

create_fifo_pipes() {
    mkdir -p "$PIPE_FOLDER_PATH"

    # Check if TOUCH_SENSOR_TO_SCREEN_PIPE already exists
    if [ -p "$TOUCH_SENSOR_TO_SCREEN_PIPE" ]; then
        echo "FIFO pipe $TOUCH_SENSOR_TO_SCREEN_PIPE already exists."
    else
        mkfifo "$TOUCH_SENSOR_TO_SCREEN_PIPE"
        echo "FIFO pipe $TOUCH_SENSOR_TO_SCREEN_PIPE created."
    fi

    # Check if NFC_TO_SCREEN_PIPE already exists
    if [ -p "$NFC_TO_SCREEN_PIPE" ]; then
        echo "FIFO pipe $NFC_TO_SCREEN_PIPE already exists."
    else
        mkfifo "$NFC_TO_SCREEN_PIPE"
        echo "FIFO pipe $NFC_TO_SCREEN_PIPE created."
    fi
}

main() {
    assert_conditions
    create_fifo_pipes
}

main