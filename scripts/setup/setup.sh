# !/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

assert_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tThis script must be run as root. Please use sudo."
        exit 1
    fi
}

load_env_variables() {
    local project_path="${SCRIPT_DIR}/../../"
    set -a
    source "${project_path}/config/scripts_config.sh" || return 1
    source "${project_path}/.env" || return 1
    set +a
}

run_scripts() {
    local target_dir="$1"
    readonly target_dir
    shift

    for script in "${target_dir}"/*.sh; do
        echo "In Progress: ${script##*/}"
        if ! bash "${script}" 2>&1; then
            echo -e "\033[0;31m[FAIL]\033[0m\t\t${script##*/}"
            exit 2
        fi
        echo -e "\033[0;32m[OK]\033[0m\t\t${script##*/}"
    done
}

run_pre_reboot_tasks() {
    if [ ! -f "${PRE_REBOOT_FLAG_FILE}" ]; then
        echo "Initiating pre-reboot setup..."
        run_scripts "${SCRIPT_DIR}/pre-reboot"
    else
        echo -e "\033[0;33m[WARNING]\033[0m\tPre-reboot setup already completed."
        exit 0
    fi
    echo "Pre-reboot tasks completed. Do you wish to reboot now? (Y/n)"
    
    local response
    while true; do
        read response
        case "${response}" in
            [Yy])
                # Create file locks and flags required during post-reboot setup
                mkdir "${PROJECT_PATH}/app/locks" 2> /dev/null
                mkdir "${PROJECT_PATH}/app/flags" 2> /dev/null
                touch "${DISPLAY_FRAME_BUFFER_LOCK_PATH}"
                touch "${PRE_REBOOT_FLAG_FILE}"

                reboot
                ;;
            [Nn])
                echo -e "\033[0;33m[WARNING]\033[0m\tPost-reboot setup wont begin until system is rebooted."
                break
                ;;
            *)
                echo "Invalid input. Please answer 'Y' (yes) or 'n' (no)."
                ;;
        esac
    done
    exit 0
}

run_post_reboot_tasks() {
    echo "Checking post-reboot requirements..."
    if [ ! -f "${PRE_REBOOT_FLAG_FILE}" ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tPre-reboot dependencies missing."
        exit 1
    elif [ -f "${POST_REBOOT_FLAG_FILE}" ]; then
        echo -e "\033[0;33m[WARNING]\033[0m\tPost-reboot setup already completed."
        exit 0
    fi

    echo -e "\nInitiating post-reboot setup..."
    run_scripts "${SCRIPT_DIR}/post-reboot"
    touch "${POST_REBOOT_FLAG_FILE}"
    
    echo -e "\033[1mFiberPTS\033[0m] setup is done. System will reboot now."
    reboot
}   

print_usage() {
    echo "Usage: $0 --pre | --post"
}

main() {
    assert_root
    load_env_variables

    if [ "$#" -ne 1 ]; then
        print_usage
        exit 1
    fi

    case "$1" in
        --pre)
            run_pre_reboot_tasks
            ;;
        --post)
            run_post_reboot_tasks
            ;;
        *)
            echo "$0: Invalid option '$1'"
            print_usage
            exit 1
            ;;
    esac
    exit 0
}

main "$@"