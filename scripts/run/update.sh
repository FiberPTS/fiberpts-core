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

load_env_variables() {
    set -a
    source "$SCRIPT_DIR/../../scripts/paths.sh" || return 1
    source "$SCRIPT_DIR/../../.env" || return 1
    set +a
}

# TODO: Test if this works since may need to do a hard reset first
pull_latest_changes() {
    echo "Pulling latest changes from $GIT_BRANCH branch..."
    git -C "$PROJECT_PATH" pull origin "$GIT_BRANCH" || { echo "Git pull failed" >&2; return 1; }
}

run_scripts() {
    local scripts=("${@:1}")

    for script in "${scripts[@]}"; do
        echo "Running script: $script"
        if ! bash "$SETUP_DIR/$script" 2>&1; then
            echo -e "\nError executing $script. Exiting." >&2
            exit 1
        fi
        echo "Completed.\n"
    done

    echo -e "\nFinished update"
}

print_usage() {
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
                print_usage
                ;;
            :)
                echo "Option -$OPTARG requires an argument." >&2
                print_usage
                ;;
        esac
    done
}

main() {
    local scripts=("post-reboot/set_user_permissions.sh" "pre-reboot/create_services.sh")

    assert_conditions
    parse_arguments
    load_env_variables
    pull_latest_changes || exit 1
    run_scripts "${scripts[@]}"
}

main