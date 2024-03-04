#!/bin/bash

# This tells the shell to exit the script if any command within the script exits with a non-zero status
set -e

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${WARNING_MSG} This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "${PROJECT_PATH}" ]; then
        echo -e "${WARNING_MSG} Required environment variable PROJECT_PATH is not set."
        exit 1
    fi

    if [ ! -d "${PROJECT_PATH}/venv" ]; then
        echo -e "${WARNING_MSG} Virtual environment not found at ${PROJECT_PATH}/venv. Please create it before running this script."
        exit 1
    fi
}

install_python_packages() {
    local py_req_file="${PROJECT_PATH}/requirements.txt"
    if [ -f "${py_req_file}" ]; then
        echo "Installing Python packages..."
        "${PROJECT_PATH}/venv/bin/pip3" install -r "${py_req_file}" || { echo "Failed to install Python packages"; return 1; }
    else
        echo -e "${WARNING_MSG} Python requirements file not found: ${py_req_file}"
        return 1
    fi
}

install_unix_packages() {
    # Required for parsing JSON and extract first device ID
    apt-get install jq -y
}

main() {
    assert_conditions
    install_unix_packages || { echo -e "${FAIL_MSG} Failed to install Python dependencies."; exit 1; }
    install_python_packages || { echo -e "${FAIL_MSG} Failed to install Python dependencies."; exit 1; }
    echo -e "${OK_MSG} All Python dependencies installed successfully"
}

main
