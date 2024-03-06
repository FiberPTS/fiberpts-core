#!/bin/bash

set -e

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${WARNING_MSG} This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "${PIPE_FOLDER_PATH}" ] || [ -z "${TOUCH_SENSOR_TO_SCREEN_PIPE}" ] || [ -z "${NFC_TO_SCREEN_PIPE}" ]; then
        echo -e "${WARNING_MSG} Required environment variables PIPE_FOLDER_PATH, TOUCH_SENSOR_TO_SCREEN_PIPE, or NFC_TO_SCREEN_PIPE are not set."
        exit 1
    fi
}

create_fifo_pipes() {
    echo -e "Creating FIFO pipes..."

    if [ -p "${TOUCH_SENSOR_TO_SCREEN_PIPE}" ]; then
        echo -e "${WARNING_MSG} FIFO pipe '${TOUCH_SENSOR_TO_SCREEN_PIPE}' already exists."
    else
        echo -e "${OK_MSG} FIFO pipe '${TOUCH_SENSOR_TO_SCREEN_PIPE}' created."
        mkfifo "${TOUCH_SENSOR_TO_SCREEN_PIPE}"
    fi
             
    if [ -p "${NFC_TO_SCREEN_PIPE}" ]; then
        echo -e "${WARNING_MSG} FIFO pipe '${NFC_TO_SCREEN_PIPE}' already exists."
    else
        echo -e "${OK_MSG} FIFO pipe '${NFC_TO_SCREEN_PIPE}' created."
        mkfifo "${NFC_TO_SCREEN_PIPE}"
    fi
}

main() {
    assert_conditions
    create_fifo_pipes
}

main