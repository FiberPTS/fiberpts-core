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

install_libretech_wiring_tool() {
    if [ ! -d "$PROJECT_DIR/libretech-wiring-tool" ]; then
        git clone https://github.com/libre-computer-project/libretech-wiring-tool.git "$PROJECT_DIR/libretech-wiring-tool" || { echo "Git clone failed"; exit 1; }
        sh "$PROJECT_DIR/libretech-wiring-tool/install.sh" || { echo "Install script failed"; exit 1; }
        "$PROJECT_DIR/libretech-wiring-tool/ldto" merge uart-a spi-cc-cs1 spi-cc-1cs-ili9341 || { echo "ldto merge command failed"; exit 1; }
    fi
}

main() {
    assert_conditions
    install_libretech_wiring_tool
}

main
