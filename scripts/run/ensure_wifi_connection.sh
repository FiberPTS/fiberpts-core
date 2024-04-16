#!/bin/bash

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
  source "${SCRIPT_DIR}/../../scripts/globals.sh" || return 1
}

#######################################
# Check if the Internet is reachable.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 if the internet is reachable, 1 otherwise.
#######################################
function check_internet() {
    # Use 8.8.8.8 as the IP for Google's DNS, a common choice for a connectivity test
    ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1
    return $?
}

#######################################
# Dynamically manage specified systemd services based on internet connectivity status.
# Globals:
#   None
# Arguments:
#   1. An array of service names to manage
# Outputs:
#   Outputs service management status.
# Returns:
#   None
#######################################
function manage_services() {
    local services=("$@")  # Accept multiple arguments as an array of service names

    local internet_status
    check_internet
    internet_status=$?

    for service_name in "${services[@]}"; do
        if (( internet_status == 0 )); then
            echo "Internet is up - ensuring service ${service_name} is running."
            systemctl is-active --quiet "${service_name}" || systemctl start "${service_name}"
        else
            echo "Internet is down - stopping service ${service_name}."
            systemctl is-active --quiet "${service_name}" && systemctl stop "${service_name}"
        fi
    done
}

#######################################
# Main execution loop.
# Globals:
#   CHECK_INTERVAL
# Arguments:
#   None
# Outputs:
#   Logs status of environment variable loading and service management.
# Returns:
#   None
#######################################
while true; do
    load_env_variables || { echo "Failed to load environment variables."; exit 1; }

    # Define an array of service filenames
    local services=("nfc_reader" "touch_sensor" "screen")

    # Pass the array to manage_services
    manage_services "${services[@]}"
    
    sleep "${CHECK_INTERVAL}"  # Sleep for a configurable number of seconds
done
