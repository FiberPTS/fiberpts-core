#!/bin/bash

assert_conditions() {
    if [ -z "$WIFI_NAME" ] || [ -z "$WIFI_PSK" ]; then
        echo "Environment variables WIFI_NAME or WIFI_PSK are not set."
    fi
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
            echo "Connected successfully to $WIFI_NAME."
        elif [ $status -eq 1 ]; then
            # General errors (e.g., Wi-Fi is turned off)
            echo "An error occurred. Unable to connect to $WIFI_NAME."
        elif [ $status -eq 2 ]; then
            if [ $attempt -eq 1 ]; then
                echo "Please enter the Wi-Fi credentials."
            elif [ $attempt -gt 1 ]; then
                echo "Invalid SSID or password. Please enter credentials again."
            fi
            echo -n "Enter Wi-Fi Name: "
            read WIFI_NAME
            echo -n "Enter Wi-Fi Password: "
            read -s WIFI_PSK
            echo
        else
            # Other errors
            echo "An unexpected error occurred. Unable to connect."
        fi
    done

    if [ "$success" = false ]; then
        echo "Failed to connect after $max_attempts attempts."
    else
        nmcli connection modify "$WIFI_NAME" connection.autoconnect yes
    fi
}

main() {
    assert_conditions
    connect_wifi
}

main