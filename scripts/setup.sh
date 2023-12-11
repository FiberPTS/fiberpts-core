#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi

    # Argument count check
    if [ "$#" -ne 2 ]; then
        echo "Usage: $0 wifi_name wifi_pwd"
        exit 1
    fi
}

install_apt_dependencies() {
    apt-get update && apt-get install -y python3-pip python3-venv || {
            echo "Failed to install dependencies. Exiting."
            exit 1
        }
}

load_env_variables() {
    set -a # Exports all environment variables
    WIFI_NAME="$1"
    WIFI_PSK="$2"
    source "$SCRIPT_DIR/../.env.shared" || return 1
    source "$SCRIPT_DIR/../.env" || return 1
    set +a # Stops exporting environment variables
}

setup_cron_job() {
    local job_command="$SCRIPT_DIR/$(basename $0) $WIFI_NAME $WIFI_PSK"
    (crontab -l 2>/dev/null; echo "@reboot $job_command") | crontab -
    echo "Cron job set for next reboot."
}

cleanup_after_reboot() {
    # Cleanup
    crontab -l | grep -v "$SCRIPT_DIR" | crontab -
    rm -f "$FLAG_FILE"
    echo "Cleanup complete."
}

run_scripts() {
    local phase=$1
    local scripts=("${@:2}")

    for script in "${scripts[@]}"; do
        echo "Running script: $script"
        if ! bash "$SETUP_DIR/$script" 2>&1; then
            echo -e "\nError executing $script. Exiting."
            exit 1
        fi
        echo "Fin"
    done

    echo -e "\n$phase Phase Complete"
}

assert_conditions "$@"
load_env_variables "$@" || {
    echo "Failed to load environment variables. Exiting."
    exit 1
}

FLAG_FILE="$PROJECT_PATH/app/exec_pre_install"
SETUP_DIR="$SCRIPT_DIR/setup"

PRE_REBOOT_SCRIPTS=("create_venv.sh" "install_dependencies.sh" "install_wifi_driver.sh" "set_device_overlays.sh" "create_services.sh")
POST_REBOOT_SCRIPTS=("create_pipes.sh" "set_user_permissions.sh" "connect_wifi.sh")

main() {
    # Phase 1: Pre Reboot
    if [ ! -f "$FLAG_FILE" ]; then
        install_apt_dependencies
        run_scripts "Pre-Reboot" "${PRE_REBOOT_SCRIPTS[@]}"
        setup_cron_job
        touch "$FLAG_FILE"
        reboot
    fi

    # Phase 2: Post Reboot
    if [ -f "$FLAG_FILE" ]; then
        run_scripts "Post-Reboot" "${POST_REBOOT_SCRIPTS[@]}"
        cleanup_after_reboot
    fi
    
    echo "Based."
}

main
