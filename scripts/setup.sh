#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

assert_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi
}

load_env_variables() {
    set -a
    source "$SCRIPT_DIR/../config/scripts_config.sh" || return 1
    source "$SCRIPT_DIR/../.env" || return 1
    set +a
}

run_scripts() {
    local target_dir="$1"
    shift

    for script in "$target_dir"/*.sh; do
        echo -e "[In Progress]\t${script##*/}"
        if ! bash "$setup_dir/$script" 2>&1; then
            echo -e "\033[0;31m[FAIL]\033[0m\t\t${script##*/}"
            exit 2
        fi
        echo -e "\033[0;32m[OK]\033[0m\t\t${script##*/}"
    done
}

print_usage() {
    echo "Usage: $0 [-s script1.sh script2.sh ...] [-n wifi_name -p wifi_pwd]"
    exit 1
}

parse_arguments() {
    local scripts_provided=false
    local scripts_to_run=()
    WIFI_NAME=""
    WIFI_PSK=""

    while getopts ":n:p:s:" opt; do
        case $opt in
            n) WIFI_NAME="$OPTARG";;
            p) WIFI_PSK="$OPTARG";;
            s) scripts_provided=true; scripts_to_run+=("$OPTARG");;
            \?) echo "Invalid option -$OPTARG" >&2; print_usage;;
        esac
    done
    shift $((OPTIND-1))

    load_env_variables

    if [ "$scripts_provided" = true ]; then
        scripts_to_run+=("$@")
        run_scripts "$SCRIPT_DIR/setup" "${scripts_to_run[@]}"
        exit 0
    fi

    # Check that either -s or both -n and -p are provided
    if [ -z "$WIFI_NAME" ] || [ -z "$WIFI_PSK" ]; then
        print_usage
    fi
}

main() {
    assert_root
    parse_arguments "$@"

    local fb_lock_flag_file_path="$DISPLAY_FRAME_BUFFER_LOCK_PATH"
    local pre_reboot_flag_file_path="$PROJECT_PATH/app/tmp/pre_reboot_installed"
    
    local pre_reboot_scripts=(
        "create_venv.sh" 
        "install_dependencies.sh" 
        "set_device_overlays.sh" 
        "install_wifi_driver.sh" 
        "create_pipes.sh" 
        "create_services.sh"
    )

    local post_reboot_scripts=(
        "set_device_overlays.sh" 
        "connect_wifi.sh" 
        "set_user_permissions.sh"
    )

    if [ ! -f "$pre_reboot_flag_file_path" ]; then
        run_scripts "$SCRIPT_DIR/setup" "${pre_reboot_scripts[@]}"
        # setup_cron_job
        mkdir -p "$PROJECT_PATH/app/tmp"
        touch "$fb_lock_flag_file_path"
        touch "$pre_reboot_flag_file_path"
        echo "Pre-Reboot Phase Complete"
    else
        run_scripts "$SCRIPT_DIR/setup" "${post_reboot_scripts[@]}"
        cleanup_after_reboot "$pre_reboot_flag_file_path"
        echo "Post-Reboot Phase Complete"
    fi

    echo "Based."
    reboot
}

main "$@"