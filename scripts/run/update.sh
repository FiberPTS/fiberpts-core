#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SETUP_DIR="$SCRIPT_DIR/../setup"

assert_conditions() {
    # Root check
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Please use sudo."
        exit 1
    fi
}

# For updating the device with new repository changes
load_env_variables() {
    set -a # Exports all environment variables
    source "$SCRIPT_DIR/../../app/.env.shared" || return 1
    source "$SCRIPT_DIR/../../app/.env" || return 1
    set +a # Stops exporting environment variables
}

run_scripts() {
    local scripts=("${@:1}")

    for script in "${scripts[@]}"; do
        echo "Running script: $script"
        if ! bash "$SETUP_DIR/$script" 2>&1; then
            echo -e "\nError executing $script. Exiting."
            exit 1
        fi
        echo "Fin"
    done

    echo -e "\nFinished update"
}

SCRIPTS=("set_user_permissions.sh" "create_services.sh")

main() {
    assert_conditions
    load_env_variables
    run_scripts "${SCRIPTS[@]}"
}

main