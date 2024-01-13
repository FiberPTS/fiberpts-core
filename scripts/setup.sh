#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

assert_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi
}

load_env_variables() {
    set -a # Exports all environment variables
    [ -n "$WIFI_NAME" ] && export WIFI_NAME
    [ -n "$WIFI_PSK" ] && export WIFI_PSK

    source "$SCRIPT_DIR/../app/.env.shared" || return 1
    source "$SCRIPT_DIR/../app/.env" || return 1
    set +a # Stops exporting environment variables
}

run_scripts() {
    local setup_dir="$1"
    shift
    local scripts=("$@")

    for script in "${scripts[@]}"; do
        echo "Running script: $script"
        if ! bash "$setup_dir/$script" 2>&1; then
            echo -e "\nError executing $script. Exiting."
            exit 1
        fi
    done

    echo -e "\nScripts Execution Complete"
}

setup_cron_job() {
    local script_name="$SCRIPT_DIR/$(basename $0)"
    local job_command="bash $script_name -n \"$WIFI_NAME\" -p \"$WIFI_PSK\" 2>&1 | /bin/systemd-cat -t $(basename $0)"
   
    if crontab -l 2>/dev/null | grep -Fq "$script_name"; then
        echo "Cron job already exists. Skipping."
    else
        (crontab -l 2>/dev/null; echo "@reboot $job_command") | crontab -
        echo "Cron job set for next reboot."
    fi
}

cleanup_after_reboot() {
    local pre_reboot_flag_file_path="$1"
    crontab -l | grep -v "$SCRIPT_DIR" | crontab -
    rm -f "$pre_reboot_flag_file_path"
    echo "Cleanup complete."
}

parse_arguments() {
    local scripts_flag=false
    local scripts_to_run=()
    WIFI_NAME=""
    WIFI_PSK=""

    while getopts ":n:p:s:" opt; do
        case $opt in
            n) WIFI_NAME="$OPTARG";;
            p) WIFI_PSK="$OPTARG";;
            s) scripts_flag=true; scripts_to_run+=("$OPTARG");;
            \?) echo "Invalid option -$OPTARG" >&2; exit 1;;
        esac
    done
    shift $((OPTIND-1))

    load_env_variables

    if [ "$scripts_flag" = true ]; then
        scripts_to_run+=("$@")
        run_scripts "$SCRIPT_DIR/setup" "${scripts_to_run[@]}"
        exit 0
    fi

    # Check that either -s or both -n and -p are provided
    if [ -z "$WIFI_NAME" ] || [ -z "$WIFI_PSK" ]; then
        echo "Usage: $0 [-s script1.sh script2.sh ...] [-n wifi_name -p wifi_pwd]"
        exit 1
    fi
}

main() {
    assert_root
    parse_arguments "$@"

    local pre_reboot_flag_file_path="$PROJECT_PATH/app/tmp/pre_reboot_installed"
    local pre_reboot_scripts=("create_venv.sh" "install_dependencies.sh" "set_device_overlays.sh" "install_wifi_driver.sh" "create_pipes.sh" "set_user_permissions.sh" "create_services.sh")
    local post_reboot_scripts=("set_device_overlays.sh" "connect_wifi.sh")

    if [ ! -f "$pre_reboot_flag_file_path" ]; then
        run_scripts "$SCRIPT_DIR/setup" "${pre_reboot_scripts[@]}"
        setup_cron_job
        mkdir -p "$PROJECT_PATH/app/tmp"
        touch "$pre_reboot_flag_file_path"
        echo "Pre-Reboot Phase Complete"
    else
        run_scripts "$SCRIPT_DIR/setup" "${post_reboot_scripts[@]}"
        cleanup_after_reboot "$pre_reboot_flag_file_path"
        echo "Post-Reboot Phase Complete"
    fi

    echo "Based."
    /usr/sbin/reboot
}

main "$@"