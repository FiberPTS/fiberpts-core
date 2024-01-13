#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "$PROJECT_DIR" ] || [ -z "$PROJECT_PATH" ]; then
        echo "Required environment variable PROJECT_DIR is not set."
        exit 1
    fi
}

set_custom_dts() {
    cp "$PROJECT_PATH/custom/spi-cc-1cs-ili9341.dts" "$PROJECT_DIR/libretech-wiring-tool/libre-computer/aml-s905x-cc/dt/spi-cc-1cs-ili9341.dts" || { echo "Install script failed"; exit 1; }
}

install_libretech_wiring_tool() {
    local pre_reboot_flag_file_path=$1
    local overlay_merged_flag_file_path=$2

    if [ ! -f "$pre_reboot_flag_file_path" ] ; then
        if [ ! -d "$PROJECT_DIR/libretech-wiring-tool" ]; then
            git clone https://github.com/libre-computer-project/libretech-wiring-tool.git "$PROJECT_DIR/libretech-wiring-tool" || { echo "Git clone failed"; exit 1; }
            set_custom_dts
            bash "$PROJECT_DIR/libretech-wiring-tool/install.sh" || { echo "Install script failed"; exit 1; }
        fi
    fi
    if [ -f "$pre_reboot_flag_file_path" ] ; then
        if [ -d "$PROJECT_DIR/libretech-wiring-tool" ]; then
            if [ ! -f "$overlay_merged_flag_file_path" ]; then
                touch "$overlay_merged_flag_file_path"
                /opt/libretech-wiring-tool/ldto merge uart-a spi-cc-cs1 spi-cc-1cs-ili9341 || { echo "ldto merge command failed"; exit 1; }
            fi
            if [ -f "$overlay_merged_flag_file_path" ]; then
                rm -f "$overlay_merged_flag_file_path"
                /opt/libretech-wiring-tool/ldto reset || { echo "ldto merge command failed"; exit 1; }
                echo "To merge the overlays, you must first reboot, then run this script again."
            fi
        fi
    fi
}

main() {
    local pre_reboot_flag_file_path="$PROJECT_PATH/app/tmp/pre_reboot_installed"
    local overlay_merged_flag_file_path="$PROJECT_PATH/app/tmp/overlay_merged"

    assert_conditions
    install_libretech_wiring_tool "$pre_reboot_flag_file_path" "$overlay_merged_flag_file_path"
}

main
