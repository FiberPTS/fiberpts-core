#!/bin/bash

# Monitors system logs for specific display driver errors (panel-ilitek-ili9341
# and spi_master) and resets the display drivers when a certain number of these
# errors occur within a predefined time frame. Reset operation is performed
# safely by using a file-descriptor-based locking mechanism.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISPLAY_ERROR_MESSAGE="panel-ilitek-ili9341.*SPI transfer failed|spi_master.*failed to transfer one message from queue|panel-ilitek-ili9341.*\*ERROR\* Failed to update display"
DISPLAY_ERROR_COUNT_THRESHOLD=4
readonly SCRIPT_DIR DISPLAY_ERROR_MESSAGE DISPLAY_ERROR_COUNT_THRESHOLD

source "${SCRIPT_DIR}/../../scripts/paths.sh"
exec 200> "${DISPLAY_FRAME_BUFFER_LOCK_PATH}"

# Unlock file descriptor 200 on script exit
trap 'flock -u 200' EXIT

error_count=0
last_error_timestamp=$(dmesg | grep -E "${DISPLAY_ERROR_MESSAGE}" | tail -1 | grep -oP '\[\s*\K\d+\.\d+')

if [ -z "${last_error_timestamp}" ]; then
  last_error_timestamp=0
else
  initial_errors=$(dmesg | grep -c -E "${DISPLAY_ERROR_MESSAGE}")
  error_count=$((initial_errors % error_count_threshold))
fi

dmesg --follow | while read line; do
  if echo "${line}" | grep -q -E "${DISPLAY_ERROR_MESSAGE}"; then
    new_error_timestamp=$(echo "${line}" | grep -oP '\[\s*\K\d+\.\d+')
    if (($(echo "${new_error_timestamp} > ${last_error_timestamp}" | bc -l))); then
      ((error_count++))
      if [ "${error_count}" -gt "${DISPLAY_ERROR_COUNT_THRESHOLD}" ]; then
        flock -x 200
        rmmod ili9341 # Unload ili9341 driver
        sleep 0.5
        modprobe ili9341 # Reload ili9341 driver
        sleep 0.5
        flock -u 200
        error_count=0
      fi
    fi
  fi
done
