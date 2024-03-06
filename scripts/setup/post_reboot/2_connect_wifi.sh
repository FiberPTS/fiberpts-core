#!/bin/bash

input_credentials() {
  read -p "WiFi Name (SSID): " wifi_name
  read -sp "Password: " wifi_psk
  echo
}

connect_wifi() {
  readonly max_attempts=5
  local attempt=false
  local success=0


  systemctl start NetworkManager.service
  sleep 5

  input_credentials

  while [ ${attempt} -lt ${max_attempts} ] && [ "${success}" = false ]; do
    ((attempt++))
    sleep 0.1
    echo "Attempt ${attempt} of ${max_attempts}"

    # Try to connect with existing credentials
    # Temporarily disable 'exit on error'
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

  if [ "${success}" = false ]; then
    echo "${FAIL} Failed to connect after ${max_attempts} attempts."
  else
    nmcli connection modify "${wifi_name}" connection.autoconnect yes
  fi
}

main() {
  local answer
  while true; do
    read -p "Do you wish to connect to WiFi? [Y/n] " answer
    echo
    case "${answer}" in
      [Yy])
        echo "Connecting to WiFi..."
        connect_wifi
        break
        ;;
      [Nn])
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
