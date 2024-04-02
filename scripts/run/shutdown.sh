#!/bin/bash
#
# This script is a shutdown script for all application processes that does a cleanup of any resources. 
# The script is set to shutdown at a specified time each day.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

#######################################
# Checks that the script is run as root.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None or error message
# Returns:
#   Exits with status 1 when not running as root, otherwise 0 on success.
#######################################
function assert_root() {
  # Root check
  if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Please use sudo."
    exit 1
  fi
}

#######################################
# Sources the relevant environment variables.
# Globals:
#   SCRIPT_DIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   1 when sourcing fails, otherwise 0 on success.
#######################################
function load_env_variables() {
  source "${SCRIPT_DIR}/../../scripts/paths.sh" || return 1
  source "${SCRIPT_DIR}/../../config/config.sh" || return 1
}

#######################################
# Checks if the current time has passed the timestamp.
# Globals:
#   None
# Arguments:
#   timestamp - A timestamp in the form "hh:mm:ss" to be checked against the current time.
# Outputs:
#   None
# Returns:
#   1 when time has not passed, and 0 otherwise.
#######################################
function check_time() {
    local timestamp="$1"
    readonly timestamp
    local now=$(date +"%T")
    if [[ "$now" > "$timestamp" ]] || [[ "$timestamp" == "$now" ]]; then
        return 0
    else
        return 1
    fi
}

#######################################
# Cleans up any resources used by the application.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   1 when cleanup fails, otherwise 0 on success.
#######################################
function cleanup() {
    return 0
}

#######################################
# The main loop of the program.
# Globals:
#   SHUTDOWN_TIME
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   1 when cleanup fails, otherwise 0 on success.
#######################################
function main() {
    assert_root
    load_env_variables
    while true; do
        sleep 60
        if check_time "$SHUTDOWN_TIME"; then
            echo "Shutdown Initiated"
            if cleanup; then
                shutdown now -h
            fi
        fi
    done
}

main