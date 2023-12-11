#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi
    
    if [ -z "$PROJECT_DIR" ]; then
        echo "Required environment variable PROJECT_DIR is not set."
        exit 1
    fi
}

install_rtl8812au_driver() {
    cd "$PROJECT_DIR" || { echo "Failed to change directory to $PROJECT_DIR"; exit 1; }
    git clone -b v5.6.4.2 https://github.com/aircrack-ng/rtl8812au.git || { echo "Git clone failed"; exit 1; }
    cd rtl8812au || { echo "Failed to change directory to rtl8812au"; exit 1; }
    make dkms_install || { echo "make dkms_install failed"; exit 1; }
}

main() {
    assert_conditions
    install_rtl8812au_driver
}

main
