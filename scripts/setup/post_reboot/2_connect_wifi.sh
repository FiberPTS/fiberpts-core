#!/bin/bash
#
# This script manages WiFi connections by prompting the user for WiFi
# credentials and attempting to connect to the specified WiFi network. It
# utilizes NetworkManager for managing network connections and nmcli for
# connection attempts.

#######################################
# Prompts the user for WiFi SSID and password.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Prompts for user input on stdout.
#######################################
function input_credentials() {
  read -p "WiFi Name (SSID): " WIFI_NAME
  read -sp "Password: " WIFI_PSK
  echo
}

#######################################
# Attempts to connect to the specified WiFi network using credentials
# provided by the user. Retries up to a maximum number of attempts.
# Globals:
#   WIFI_NAME - The SSID of the WiFi network.
#   WIFI_PSK - The password for the WiFi network.
# Arguments:
#   None
# Outputs:
#   Status messages regarding WiFi connection attempts.
# Returns:
#   Exits with status 1 on unexpected error, otherwise 0 on success.
#######################################
function connect_wifi() {
  readonly max_attempts=5
  local attempt=0
  local success=false

  systemctl start NetworkManager.service
  sleep 5  # TODO: Find a more precise method for ensuring NetworkManager is ready

  input_credentials

  while [ ${attempt} -lt ${max_attempts} ] && [ "${success}" = false ]; do
    ((attempt++))
    sleep 0.1
    echo "Attempt ${attempt} of ${max_attempts}"

    # Temporarily disable 'exit on error' for nmcli command
    set +e
    nmcli dev wifi connect "${WIFI_NAME}" password "${WIFI_PSK}"
    local status=$?
    set -e

    case ${status} in
      0)
        success=true
        echo "${OK} Connected successfully to ${WIFI_NAME}."
        ;;
      1)
        echo "Incorrect password. Please enter credentials again."
        input_credentials
        ;;
      10)
        echo "Please enter credentials again."
        input_credentials
        ;;
      *)
        echo "${FAIL} An unexpected error occurred. Unable to connect."
        exit 1
        ;;
    esac
  done

  # Enable autoconnect for the WiFi connection
  if [ "${success}" = true ]; then
    nmcli connection modify "${WIFI_NAME}" connection.autoconnect yes
  else
    echo "${FAIL} Failed to connect after ${max_attempts} attempts."
  fi
}

#######################################
# Main loop that prompts the user if they wish to connect to WiFi.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Prompts for user decision and calls connect_wifi on affirmative.
#######################################
function main() {
  while true; do
    read -p "Do you wish to connect to WiFi? [Y/n] " answer
    echo
    case "${answer}" in
      [Yy]*)
        echo "Connecting to WiFi..."
        connect_wifi
        break
        ;;
      [Nn]*)
        echo "Run this script if you wish to connect to WiFi. Exiting..."
        break
        ;;
      *)
        echo "Invalid input. Please answer 'Y' (yes) or 'n' (no)."
        ;;
    esac
  done
}

main
