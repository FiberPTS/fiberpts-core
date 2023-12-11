#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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

main() {
    assert_conditions
    load_env_variables
    bash "$SCRIPT_DIR/../setup/set_user_permissions.sh"
}

main