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

    export MAINPID=''

    for service_template in "$service_dir"/*.service; do
        local service_filename=$(basename "$service_template")
        envsubst < "$service_template" > "$SYSTEMD_DIR/$service_filename"
        echo "Service file created: $service_filename"
        systemctl enable "$service_filename"
        echo "Service file enabled: $service_filename"
    done

    echo "All service files are now processed and services enabled."
}

main() {
    assert_conditions
    process_service_files
}

main
