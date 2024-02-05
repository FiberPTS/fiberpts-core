#!/bin/bash

assert_conditions() {
    if [ -z "$WIFI_NAME" ] || [ -z "$WIFI_PSK" ]; then
        echo "Environment variables WIFI_NAME or WIFI_PSK are not set."
        input_credentials "Please enter the Wi-Fi credentials."
    fi
}

input_credentials() {
    echo "$1"
    read -p "Enter WiFi network name (SSID): " WIFI_NAME
    read -sp "Password: " WIFI_PSK
    echo
}

connect_wifi() {
    local attempt=0
    local max_attempts=5
    local success=false
    systemctl start NetworkManager.service
    sleep 5
    while [ $attempt -lt $max_attempts ] && [ "$success" = false ]; do
        ((attempt++))
        sleep 0.1
        echo "Attempt $attempt of $max_attempts"

        # Try to connect with existing credentials
        # Temporarily disable 'exit on error'
        set +e
        nmcli dev wifi connect "$WIFI_NAME" password "$WIFI_PSK"
        local status=$?
        set -e

        if [ $status -eq 0 ]; then
            success=true
            echo "\033[0;32m[OK]\033[0m\t\tConnected successfully to $WIFI_NAME."
        elif [ $status -eq 1 ]; then
            input_credentials "Incorrect password. Please enter credentials again."
        elif [ $status -eq 10 ]; then
            input_credentials "Please enter credentials again."
        else
            echo "An unexpected error occurred. Unable to connect."
        fi
    done

    if [ "$success" = false ]; then
        echo "\033[0;31m[FAIL]\033[0m\t\tFailed to connect after $max_attempts attempts."
    else
        nmcli connection modify "$WIFI_NAME" connection.autoconnect yes
    fi
}

main() {
    assert_conditions

    local answer
    while true; do
        read -p "Do you wish to connect to WiFi? (Y/n)" user_input
        echo
        case "${answer}" in
            [Yy] ) echo "Connecting to WiFi...";
                connect_wifi
                break
                ;;
            [Nn] ) echo "Run this script if you wish to connect to WiFi.";
                break
                ;;
            * )    echo "Invalid input. Please answer 'Y' (yes) or 'n' (no)."
                ;;
        esac
    done
}

main