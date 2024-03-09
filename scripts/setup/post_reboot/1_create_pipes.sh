#!/bin/bash
#
# Sets up the necessary FIFO pipes for communication between touch sensors, NFC
# devices, and the display screen.

set -e

#######################################
# Verifies that all required environment variables are set. 
# Exits if any condition is not met.
# Globals:
#   PIPE_FOLDER_PATH
#   TOUCH_SENSOR_TO_SCREEN_PIPE
#   NFC_TO_SCREEN_PIPE
# Arguments:
#   None
# Outputs:
#   Writes warning to stdout exits with status 1 on failure.
#######################################
function assert_variables() {
  local missing_env_variables
  if [ -z "${PIPE_FOLDER_PATH}" ]; then
    missing_env_variables+=("PIPE_FOLDER_PATH")
  fi
  if [ -z "${TOUCH_SENSOR_TO_SCREEN_PIPE}" ]; then
    missing_env_variables+=("TOUCH_SENSOR_TO_SCREEN_PIPE")
  fi
  if [ -z "${NFC_TO_SCREEN_PIPE}" ]; then
    missing_env_variables+=("NFC_TO_SCREEN_PIPE")
  fi
  if [ ${#missing_env_variables[@]} -gt 0 ]; then
    echo "${WARNING} Required environment variables ${missing_env_variables[*]} are not set."
    exit 1
  fi
}

#######################################
# Creates FIFO pipes for touch sensor and NFC device communication with the
# screen.
# Globals:
#   TOUCH_SENSOR_TO_SCREEN_PIPE
#   NFC_TO_SCREEN_PIPE
# Arguments:
#   None
# Outputs:
#   Writes status messages to stdout about FIFO pipe creation or existence.
#######################################
function create_fifo_pipes() {
  echo "Creating FIFO pipes..."

  if [ -p "${TOUCH_SENSOR_TO_SCREEN_PIPE}" ]; then
    echo "${WARNING} FIFO pipe '${TOUCH_SENSOR_TO_SCREEN_PIPE}' already exists."
  else
    mkfifo "${TOUCH_SENSOR_TO_SCREEN_PIPE}"
    echo "${OK} FIFO pipe '${TOUCH_SENSOR_TO_SCREEN_PIPE}' created."
  fi

  if [ -p "${NFC_TO_SCREEN_PIPE}" ]; then
    echo "${WARNING} FIFO pipe '${NFC_TO_SCREEN_PIPE}' already exists."
  else
    mkfifo "${NFC_TO_SCREEN_PIPE}"
    echo "${OK} FIFO pipe '${NFC_TO_SCREEN_PIPE}' created."
  fi
}

#######################################
# Main function to orchestrate script execution.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None directly, but calls functions that produce outputs.
#######################################
function main() {
  assert_variables
  create_fifo_pipes
}

main
