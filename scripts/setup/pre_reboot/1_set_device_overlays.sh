#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${WARNING_MSG} This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "${PROJECT_DIR}" ] || [ -z "${PROJECT_PATH}" ] || [ -z "${OVERLAY_MERGED_FLAG}" ]; then
        echo -e "${WARNING_MSG} Required environment variables PROJECT_DIR, PROJECT_PATH, and OVERLAY_MERGED_FLAG is not set."
        exit 1
    fi
}

set_custom_dts() {
    cp "${PROJECT_PATH}/custom/spi-cc-1cs-ili9341.dts" "${PROJECT_DIR}/libretech-wiring-tool/libre-computer/aml-s905x-cc/dt/spi-cc-1cs-ili9341.dts" || { echo "Install script failed"; exit 1; }
}

reset_overlays() {
    local answer
    while true; do
        read -p "Do you want to reset the overlays [Y/n] ?" answer
        echo
        readonly answer

        case "${answer}" in
            [Yy] ) echo "Resetting overlays...";
                rm -f "${OVERLAY_MERGED_FLAG}"
                /opt/libretech-wiring-tool/ldto reset
                echo "Overlays reset. Reboot to apply changes."
                break
                ;;
            [Nn] ) echo "Overlays not reset.";
                break
                ;;
            * )    echo "Invalid input. Please answer 'Y' (yes) or 'n' (no)."
                ;;
        esac
    done
}

merge_overlays() {
    local answer
    while true; do
        read -p "Do you want to merge the overlays [Y/n] ?" answer
        echo
        readonly answer
         
        case "${answer}" in
            [Yy] ) echo "Merging overlays...";
                /opt/libretech-wiring-tool/ldto merge uart-a spi-cc-cs1 spi-cc-1cs-ili9341 || { echo "ldto merge command failed"; exit 1; }
                echo "Overlays merged. Reboot to apply changes."
                touch "${OVERLAY_MERGED_FLAG}"
                break
                ;;
            [Nn] ) echo "Overlays not merged.";
                break
                ;;
            * )    echo "Invalid input. Please answer 'Y' (yes) or 'n' (no)"
                ;;
        esac
    done
}

install_libretech_wiring_tool() {
    if [ ! -d "${PROJECT_DIR}/libretech-wiring-tool" ]; then
        echo "Installing libretech-wiring-tool..."
        git clone https://github.com/libre-computer-project/libretech-wiring-tool.git "${PROJECT_DIR}/libretech-wiring-tool" || { echo "Git clone failed"; exit 1; }
        set_custom_dts
        bash "${PROJECT_DIR}/libretech-wiring-tool/install.sh" || { echo "Install script failed"; exit 1; }
        echo -e "${OK_MSG} Installed libretech-wiring-tool"
    else
        echo -e "${WARNING_MSG} Already installed libretech-wiring-tool."
    fi

    if [ -f "${OVERLAY_MERGED_FLAG}" ]; then
        reset_overlays
    else 
        merge_overlays
    fi
}

main() {
    assert_conditions
    install_libretech_wiring_tool
}

main
