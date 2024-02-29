# !/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

assert_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${WARNING_MSG} This script must be run as root. Please use sudo."
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
        if ! bash "${script}" 2>&1; then
            echo -e "${FAIL_MSG} ${script##*/}"
            exit 2
        fi
        echo -e "${OK_MSG} ${script##*/}"
    done
}

run_pre_reboot_tasks() {
    mkdir "${PROJECT_PATH}/.app" 2> /dev/null

    if [ ! -f "${PRE_REBOOT_FLAG}" ] && [ ! -f "${REBOOT_HALTED_FLAG}" ]; then
        echo "Initiating pre-reboot setup..."
        run_scripts "${SCRIPT_DIR}/pre_reboot"
        echo -e "Pre-reboot tasks completed."
    elif [ -f "${REBOOT_HALTED_FLAG}" ]; then
        echo -e "${WARNING_MSG} Pre-reboot setup already completed"
    elif [ -f "${PRE_REBOOT_FLAG}" ]; then
        echo -e "${WARNING_MSG} Pre-reboot setup already completed"
        exit 0
    fi
    
    mkdir "${PROJECT_PATH}/.app/flags" 2> /dev/null
    
    local response
    while true; do
        read -p "Do you wish to reboot now? [Y/n] " response
        case "${response}" in
            [Yy])
                # Create file flags and locks required during post-reboot setup
                mkdir "${PROJECT_PATH}/.app/locks" 2> /dev/null
                touch "${DISPLAY_FRAME_BUFFER_LOCK_PATH}"
                touch "${PRE_REBOOT_FLAG}"

                if [ -f "${REBOOT_HALTED_FLAG}" ]; then
                    rm -f "${REBOOT_HALTED_FLAG}"
                fi
                reboot
                ;;
            [Nn])
                touch "${REBOOT_HALTED_FLAG}"
                echo -e "${WARNING_MSG} Post-reboot setup won't begin until system is rebooted"
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
    if [ ! -f "${PRE_REBOOT_FLAG}" ]; then
        echo -e "${WARNING_MSG} Pre-reboot dependencies missing"
        exit 1
    elif [ -f "${POST_REBOOT_FLAG}" ]; then
        echo -e "${WARNING_MSG} Post-reboot setup already completed"
        exit 0
    fi
    echo -e "${OK_MSG} All requirements satisfied"

    echo -e "\nInitiating post-reboot setup..."
    run_scripts "${SCRIPT_DIR}/post_reboot"
    touch "${POST_REBOOT_FLAG}"
    
    echo -e "\n\033[1mFiberPTS\033[0m setup is done. System will reboot now."
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