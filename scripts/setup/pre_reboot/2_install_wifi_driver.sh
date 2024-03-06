#!/bin/bash

set -e

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "${WARNING} This script must be run as root. Please use sudo."
        exit 1
    fi
    
    if [ -z "${PROJECT_DIR}" ]; then
        echo "${WARNING} Required environment variable PROJECT_DIR is not set."
        exit 1
    fi
}

install_rtl8812au_driver() {
    if [ ! -d "${PROJECT_DIR}/rtl8812au" ]; then
        echo "Installing rtl8812au driver..."
        git clone -b v5.6.4.2 https://github.com/aircrack-ng/rtl8812au.git "${PROJECT_DIR}/rtl8812au" > /dev/null
        make -C "${PROJECT_DIR}/rtl8812au" dkms_install > /dev/null
    else
        echo "Driver already installed."
    fi
}

main() {
    assert_conditions
    install_rtl8812au_driver
}

main
