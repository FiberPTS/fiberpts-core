#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "\033[0;33m[WARNING]\033[0m\tThis script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "${PROJECT_PATH}" ] || [ -z "${SYSTEMD_DIR}" ]; then
        echo "\033[0;33m[WARNING]\033[0m\tRequired environment variables PROJECT_PATH or SYSTEMD_DIR are not set."
        exit 1
    fi
}

process_service_files() {
    local service_dir="${PROJECT_PATH}/services"

    export MAINPID=''

    for service_template in "${service_dir}"/*.service; do
        local service_filename=$(basename "${service_template}")
        if [ ! -f "${SYSTEMD_DIR}/${service_filename}" ]; then
            envsubst < "${service_template}" > "${SYSTEMD_DIR}/${service_filename}"
            systemctl enable "${service_filename}"
            if [ "$?" -eq 0 ]; do
                echo "\033[0;32m[OK]\033[0m\t\t'${service_filename}' enabled"
            else
                echo "\033[0;31m[FAIL]\033[0m\t\tFailed to enable '${service_filename}'"
            fi
        else
            envsubst < "${service_template}" > "${SYSTEMD_DIR}/${service_filename}"
            systemctl daemon-reload
            systemctl restart "${service_filename}"
            if [ "$?" -eq 0 ]; do
                echo "\033[0;32m[OK]\033[0m\t\t'${service_filename}' updated"
            else
                echo "\033[0;31m[FAIL]\033[0m\t\tFailed to update '${service_filename}'"
        fi
    done
}

main() {
    assert_conditions
    process_service_files
}

main
