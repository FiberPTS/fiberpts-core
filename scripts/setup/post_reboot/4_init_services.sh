#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "\t${WARNING_MSG} This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "${PROJECT_PATH}" ] || [ -z "${SYSTEMD_DIR}" ]; then
        echo -e "\t${WARNING_MSG} Required environment variables PROJECT_PATH or SYSTEMD_DIR are not set."
        exit 1
    fi
}

process_service_files() {
    local service_dir="${PROJECT_PATH}/templates"
    readonly service_dir

    for service_template in "${service_dir}"/*.service; do
        local service_filename=$(basename "${service_template}")
        readonly service_filename

        if [ ! -f "${SYSTEMD_DIR}/${service_filename}" ]; then
            envsubst < "${service_template}" > "${SYSTEMD_DIR}/${service_filename}"
            systemctl enable "${service_filename}"
            
            if [ "$?" -eq 0 ]; then
                echo -e "\t${OK_MSG} '${service_filename}' enabled"
            else
                echo -e "\t${FAIL_MSG} Failed to enable '${service_filename}'"
            fi
        else
            envsubst < "${service_template}" > "${SYSTEMD_DIR}/${service_filename}"
            systemctl daemon-reload
            systemctl restart "${service_filename}"

            if [ "$?" -eq 0 ]; then
                echo -e "\t${OK_MSG} '${service_filename}' updated"
            else
                echo -e "\t${FAIL_MSG} Failed to update '${service_filename}'"
        fi
    done
}

main() {
    assert_conditions
    process_service_files
}