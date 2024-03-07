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
  read -p "WiFi Name (SSID): " wifi_name
  read -sp "Password: " wifi_psk
  echo
}

#######################################
# Attempts to connect to the specified WiFi network using credentials
# provided by the user. Retries up to a maximum number of attempts.
# Globals:
#   wifi_name - The SSID of the WiFi network.
#   wifi_psk - The password for the WiFi network.
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
    nmcli dev wifi connect "${wifi_name}" password "${wifi_psk}"
    local status=$?
    set -e

    if [ ${status} -eq 0 ]; then
      success=true
      echo "${OK} Connected successfully to ${wifi_name}."
    elif [ ${status} -eq 1 ]; then
      echo "Incorrect password. Please enter credentials again."
      input_credentials
    elif [ ${status} -eq 10 ]; then
      echo "Please enter credentials again."
      input_credentials
    else
      echo "${FAIL} An unexpected error occurred. Unable to connect."
      exit 1
    fi
  done

  # Enable autoconnect for the WiFi connection
  if [ "${success}" = true ]; then
    nmcli connection modify "${wifi_name}" connection.autoconnect yes
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
