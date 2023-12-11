#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "$PROJECT_PATH" ] || [ -z "$SYSTEMD_DIR" ]; then
        echo "Required environment variables PROJECT_PATH or SYSTEMD_DIR are not set."
        exit 1
    fi
}

process_service_files() {
    local service_dir="$PROJECT_PATH/services"
    local service_filenames=()

    export MAINPID=''

    for service_template in "$service_dir"/*.service; do
        if [ -f "$service_template" ]; then
            local service_filename=$(basename "$service_template")
            envsubst < "$service_template" > "$SYSTEMD_DIR/$service_filename"
            service_filenames+=("$service_filename")
            echo "Service file created: $service_filename"
        else
            echo "No service templates found in $service_dir"
        fi
    done

    systemctl daemon-reload

    for service_filename in "${service_filenames[@]}"; do
        systemctl enable "$service_filename"
        echo "Service enabled: $service_filename"
    done

    echo "All service files are now processed, daemon reloaded, and services enabled."
}

main() {
    assert_conditions
    process_service_files
}

main
