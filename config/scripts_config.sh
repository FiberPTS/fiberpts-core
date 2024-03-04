# Application Paths
PROJECT_DIR=/opt
PROJECT_PATH=${PROJECT_DIR}/FiberPTS
DEVICE_STATE_FILE_PATH=${PROJECT_PATH}/.app/device_state.json

# System Path Configuration
SYSTEMD_DIR=/etc/systemd/system
DISPLAY_FRAME_BUFFER_LOCK_PATH=${PROJECT_PATH}/.app/locks/frame_buffer.lock
DISPLAY_FRAME_BUFFER_PATH=/dev/fb2
DISPLAY_ERROR_COUNT_THRESHOLD=4

# Named Pipe Paths
PIPE_FOLDER_PATH=${PROJECT_PATH}/.app/pipes
TOUCH_SENSOR_TO_SCREEN_PIPE=${PIPE_FOLDER_PATH}/touch_sensor_to_screen_pipe
NFC_TO_SCREEN_PIPE=${PIPE_FOLDER_PATH}/nfc_to_screen_pipe

# Flag File Paths
PRE_REBOOT_FLAG=${PROJECT_PATH}/.app/flags/pre_reboot_setup_done.flag
POST_REBOOT_FLAG=${PROJECT_PATH}/.app/flags/post_reboot_setup_done.flag
REBOOT_HALTED_FLAG=${PROJECT_PATH}/.app/flags/reboot_halted.flag
OVERLAY_MERGED_FLAG=${PROJECT_PATH}/.app/flags/overlay_merged.flag

# Log-related Paths
LOGROTATE_PATH=/etc/logrotate.d
LOG_FILENAME=fpts.log
LOGCONF_FILENAME=fpts_log.conf

# Status Messages
OK_MSG="${GREEN}[OK]     ${RESET}"
WARNING_MSG="${YELLOW}[WARNING]${RESET}"
FAIL_MSG="${RED}[FAIL]   ${RESET}"

#Color Support
if [ -t 1 ] && [ -n "$(tput colors)" ]; then
    RED="$(tput setaf 1)"
    GREEN="$(tput setaf 2)"
    YELLOW="$(tput setaf 3)"
    BLUE="$(tput setaf 4)"
    MAGENTA="$(tput setaf 5)"
    CYAN="$(tput setaf 6)"
    WHITE="$(tput setaf 7)"
    BOLD="$(tput bold)"
    RESET="$(tput sgr0)"
else
    # stdout does not support colors
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    MAGENTA=""
    CYAN=""
    WHITE=""
    BOLD=""
    RESET=""
fi
