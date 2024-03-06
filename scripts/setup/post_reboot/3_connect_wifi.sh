#!/bin/bash

set -e

input_credentials() {
    read -p "WiFi Name (SSID): " WIFI_NAME
    read -sp "Password: " WIFI_PSK
    echo
}

connect_wifi() {
    local attempt=0
    local max_attempts=5
    readonly max_attempts
    local success=false

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
        nmcli dev wifi connect "${WIFI_NAME}" password "${WIFI_PSK}"
        local status=$?
        set -e

        if [ ${status} -eq 0 ]; then
            success=true
            echo "${OK_MSG} Connected successfully to ${WIFI_NAME}."
        elif [ ${status} -eq 1 ]; then
            echo "Incorrect password. Please enter credentials again."
            input_credentials
        elif [ ${status} -eq 10 ]; then
            echo "Please enter credentials again."
            input_credentials
        else
            echo "${FAIL_MSG} An unexpected error occurred. Unable to connect."
            exit 1
        fi
    done

    if [ "${success}" = false ]; then
        echo "${FAIL_MSG} Failed to connect after ${max_attempts} attempts."
    else
        nmcli connection modify "${WIFI_NAME}" connection.autoconnect yes
    fi
}

main() {
    local answer
    while true; do
        read -p "Do you wish to connect to WiFi? [Y/n] " answer
        echo
        case "${answer}" in
            [Yy])
                echo "Connecting to WiFi...";
                connect_wifi
                break
                ;;
            [Nn])
                echo "Run this script if you wish to connect to WiFi. Exiting...";
                break
                ;;
            *)
                echo "Invalid input. Please answer 'Y' (yes) or 'n' (no)."
                ;;
        esac
    done
}

main