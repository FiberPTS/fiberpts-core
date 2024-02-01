#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "$PROJECT_DIR" ] || [ -z "$PROJECT_PATH" ] || [ -z "$OVERLAY_MERGED_FLAG_FILE" ]; then
        echo "Required environment variables PROJECT_DIR, PROJECT_PATH, and OVERLAY_MERGED_FLAG_FILE is not set."
        exit 1
    fi
}

set_custom_dts() {
    cp "$PROJECT_PATH/custom/spi-cc-1cs-ili9341.dts" "$PROJECT_DIR/libretech-wiring-tool/libre-computer/aml-s905x-cc/dt/spi-cc-1cs-ili9341.dts" || { echo "Install script failed"; exit 1; }
}

install_libretech_wiring_tool() {
    if [ ! -d "$PROJECT_DIR/libretech-wiring-tool" ]; then
        echo "Installing libretech-wiring-tool..."
        git clone https://github.com/libre-computer-project/libretech-wiring-tool.git "$PROJECT_DIR/libretech-wiring-tool" || { echo "Git clone failed"; exit 1; }
        set_custom_dts
        bash "$PROJECT_DIR/libretech-wiring-tool/install.sh" || { echo "Install script failed"; exit 1; }
        echo "Installed libretech-wiring-tool."
    else
        echo "Already installed libretech-wiring-tool..."
    fi
    if [ -f "$OVERLAY_MERGED_FLAG_FILE" ]; then
        local reset_answer=-1
        while [ reset_answer -ne 0 ] && [ reset_answer -ne 1 ]; do
            echo "Do you want to reset the overlays?"
            echo -n "Yes (1) or No (0): "
            read reset_answer
            if [ "$reset_answer" -eq 1 ]; then
                echo "Resetting overlays..."
                rm -f "$OVERLAY_MERGED_FLAG_FILE"
                /opt/libretech-wiring-tool/ldto reset
                echo "Overlays reset. Reboot to apply changes."
            elif [ "$reset_answer" -eq 0 ]; then
                echo "No action taken."
            else
                echo "Invalid input...Please try again."
            fi
        done
    else 
        local merge_answer=-1
        while [ merge_answer -ne 0 ] && [ merge_answer -ne 1 ]; do
            echo "Do you want to merge the overlays?"
            echo -n "Yes (1) or No (0): "
            read merge_answer
            if [ "$merge_answer" -eq 1 ]; then
                echo "Merging overlays..."
                touch "$OVERLAY_MERGED_FLAG_FILE"
                /opt/libretech-wiring-tool/ldto merge uart-a spi-cc-cs1 spi-cc-1cs-ili9341 || { echo "ldto merge command failed"; exit 1; }
                echo "Overlays merged. Reboot to apply changes."
            elif [ "$merge_answer" -eq 0 ]; then
                echo "No action taken."
            else
                echo "Invalid input...Please try again."
            fi
        done
    fi
}

main() {
    assert_conditions
    install_libretech_wiring_tool
}

main
