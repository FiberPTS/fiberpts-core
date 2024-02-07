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

print_usage() {
    echo "Usage: $0 [--pre, --post]"
    exit 1
}

main() {
    assert_root
    load_env_variables
    
    args=$(getopt --options - --longoptions "pre,post" --name "$0" -- "$@")

    # Set positional parameters to the getopt arguments
    eval set -- "${args}"

    # Invalid option provided
    if [[ $? -ne 0 ]] || [ "$1" == "--" ]; then
        print_usage
        exit 3
    fi

    while true; do
        case "$1" in
            --pre)
                if [ -f "${PRE_REBOOT_FLAG_FILE}" ]; then
                    echo -e "$0: pre-reboot setup already completed"
                    exit 0
                fi
                echo "Initiating pre-reboot setup..."
                run_scripts "${SCRIPT_DIR}/pre-reboot"
                shift
                echo -e "\n\n\033[1mPre-reeboot setup completed.\033[0m Rebooting..."

                # Create file locks and flags required during post-reboot setup
                mkdir "${PROJECT_PATH}/app/locks" 2> /dev/null
                mkdir "${PROJECT_PATH}/app/flags" 2> /dev/null
                touch "${DISPLAY_FRAME_BUFFER_LOCK_PATH}"
                touch "${PRE_REBOOT_FLAG_FILE}"
                reboot
                ;;
            --post)
                if [ ! -f "${PRE_REBOOT_FLAG_FILE}" ]; then
                    echo -e "\033[0;33m[WARNING]\033[0m\tPre-reboot dependencies missing."
                    exit 2
                elif [ -f "${POST_REBOOT_FLAG_FILE}" ]; then
                    echo -e "\033[0;33m[WARNING]\033[0m\tPost-reboot setup already completed."
                    exit 0
                fi
                echo -e "\nInitiating post-reboot setup..."
                run_scripts "${SCRIPT_DIR}/post-reboot"
                touch "${POST_REBOOT_FLAG_FILE}"
                shift
                ;;
            --)
                shift
                break
                ;;
        esac
    done
}

main "$@"
echo -e "\n\n\033[1mBased.\033[0m"