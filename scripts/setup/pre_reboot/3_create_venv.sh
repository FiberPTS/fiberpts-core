#!/bin/bash

set -e

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "${WARNING_MSG} This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "${PROJECT_PATH}" ]; then
        echo "${WARNING_MSG} Required environment variable PROJECT_PATH is not set."
        exit 1
    fi
}

create_virtual_environment() {
    if [ ! -d "${PROJECT_PATH}/venv" ]; then
        apt install python3.11-venv python3-pip -y > /dev/null
        python3 -m venv "${PROJECT_PATH}/venv" > /dev/null
        echo "${OK_MSG} Virtual environment created at '${PROJECT_PATH}/venv'"
    fi
}

# TODO: Fix implicit importing of FiberPTS modules without needing .pth file by sourcing in service files
add_path_to_pth_file() {
    local venv_dir="${PROJECT_PATH}/venv"
    local pth_file_name="fiberpts.pth"
    local pth_file_path="${venv_dir}/lib/python3.11/site-packages/${pth_file_name}"

    if [ -d "${venv_dir}" ]; then
        echo "${PROJECT_PATH}" > "${pth_file_path}"
        echo "Path added to ${pth_file_path}"
    else
        echo "${FAIL_MSG} Virtual environment directory not found."
        exit 1
    fi
}

main() {
    assert_conditions
    create_virtual_environment
    add_path_to_pth_file
}

main