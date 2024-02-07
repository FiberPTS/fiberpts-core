#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tThis script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "${PIPE_FOLDER_PATH}" ] || [ -z "${TOUCH_SENSOR_TO_SCREEN_PIPE}" ] || [ -z "${NFC_TO_SCREEN_PIPE}" ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tRequired environment variables PIPE_FOLDER_PATH, TOUCH_SENSOR_TO_SCREEN_PIPE, or NFC_TO_SCREEN_PIPE are not set."
        exit 1
    fi
}

create_fifo_pipes() {
    mkdir -p "${PIPE_FOLDER_PATH}"

    echo -e "Creating FIFO pipes..."

    if [ -p "${TOUCH_SENSOR_TO_SCREEN_PIPE}" ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tFIFO pipe '${TOUCH_SENSOR_TO_SCREEN_PIPE}' already exists."
    else
        mkfifo "${TOUCH_SENSOR_TO_SCREEN_PIPE}"
        echo -e "\033[0;32m[OK]\033[0m\t\tFIFO pipe '${TOUCH_SENSOR_TO_SCREEN_PIPE}' created."
    fi
             
    if [ -p "${NFC_TO_SCREEN_PIPE}" ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tFIFO pipe '${NFC_TO_SCREEN_PIPE}' already exists."
    else
        mkfifo "${NFC_TO_SCREEN_PIPE}"
        echo -e "\033[0;32m[OK]\033[0m\t\tFIFO pipe '${NFC_TO_SCREEN_PIPE}' created."
    fi
}

main() {
    assert_conditions
    create_fifo_pipes
}

main