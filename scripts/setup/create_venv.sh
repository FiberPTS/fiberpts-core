#!/bin/bash

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi

    if [ -z "$PROJECT_PATH" ]; then
        echo "Required environment variable PROJECT_PATH is not set."
        exit 1
    fi
}

create_virtual_environment() {
    if [ ! -d "$PROJECT_PATH/venv" ]; then
        python3 -m venv "$PROJECT_PATH/venv" || { echo "Failed to create virtual environment."; exit 1; }
        echo "Virtual environment created at $PROJECT_PATH/venv"
    fi
}

# TODO: Fix implicit importing of FiberPTS modules without needing .pth file by sourcing in service files
add_path_to_pth_file() {
    local venv_dir="$PROJECT_PATH/venv"
    local pth_file_name="fiberpts.pth"
    local pth_file_path="$venv_dir/lib/python3.11/site-packages/$pth_file_name"

    if [ -d "$venv_dir" ]; then
        echo "$PROJECT_PATH" > "$pth_file_path"
        echo "Path added to $pth_file_path"
    else
        echo "Error: Virtual environment directory not found."
        exit 1
    fi
}

main() {
    assert_conditions
    create_virtual_environment
    add_path_to_pth_file
}

main