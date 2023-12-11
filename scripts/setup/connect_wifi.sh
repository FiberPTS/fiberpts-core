#!/bin/bash

assert_conditions() {
    if [ -z "$WIFI_NAME" ] || [ -z "$WIFI_PSK" ]; then
        echo "Required environment variables WIFI_NAME or WIFI_PSK are not set."
        exit 1
    fi
}

connect_wifi() {
    nmcli dev wifi connect "$WIFI_NAME" password "$WIFI_PSK"
    nmcli connection modify "$WIFI_NAME" connection.autoconnect yes
}

main() {
    assert_conditions
    connect_wifi
}

main