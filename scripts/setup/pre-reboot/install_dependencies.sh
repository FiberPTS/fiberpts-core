#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tThis script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "${PROJECT_PATH}" ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tRequired environment variable PROJECT_PATH is not set."
        exit 1
    fi

    if [ ! -d "${PROJECT_PATH}/venv" ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tVirtual environment not found at ${PROJECT_PATH}/venv. Please create it before running this script."
        exit 1
    fi
}

install_python_packages() {
    local py_req_file="${PROJECT_PATH}/requirements.txt"
    if [ -f "${py_req_file}" ]; then
        echo "Installing Python packages..."
        "${PROJECT_PATH}/venv/bin/pip3" install -r "${py_req_file}" || { echo "Failed to install Python packages"; return 1; }
    else
        echo -e "\033[0;33m[WARNING]\033[0m\tPython requirements file not found: ${py_req_file}"
        return 1
    fi
}

main() {
    assert_conditions
    install_python_packages || { echo -e "\033[0;31m[FAIL]\033[0m\t\tFailed to install Python dependencies."; exit 1 }
    echo -e "\033[0;32m[OK]\033[0m\t\tAll Python dependencies installed successfully"
}

main
