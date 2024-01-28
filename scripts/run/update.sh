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
    source "$SCRIPT_DIR/../../config/scripts_config.sh" || return 1
    source "$SCRIPT_DIR/../../.env" || return 1
    set +a # Stops exporting environment variables
}

# TODO: Test if this works since may need to do a hard reset first
pull_latest_changes() {
    echo "Pulling latest changes from $GIT_BRANCH branch..."
    git -C "$PROJECT_PATH" pull origin "$GIT_BRANCH" || { echo "Git pull failed"; return 1; }
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

usage() {
    echo "Usage: $0 [-b branch_name]"
    exit 1
}

parse_arguments() {
    while getopts ":b:" opt; do
        case $opt in
            b)
                GIT_BRANCH="$OPTARG"
                ;;
            \?)
                echo "Invalid option: -$OPTARG" >&2
                usage
                ;;
            :)
                echo "Option -$OPTARG requires an argument." >&2
                usage
                ;;
        esac
    done
}

main() {
    local scripts=("set_user_permissions.sh" "create_services.sh")

    assert_conditions
    load_env_variables
    pull_latest_changes || exit 1
    run_scripts "${scripts[@]}"
}

main