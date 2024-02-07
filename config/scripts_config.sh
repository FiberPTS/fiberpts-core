# Application Path Configuration
PROJECT_DIR=/home/jbesoto/git #/opt
PROJECT_PATH=${PROJECT_DIR}/FiberPTS
DEVICE_STATE_FILE_PATH=${PROJECT_PATH}/app/device_state.json

# System Path Configuration
SYSTEMD_DIR=/etc/systemd/system
DISPLAY_FRAME_BUFFER_LOCK_PATH=${PROJECT_PATH}/app/locks/frame_buffer.lock
DISPLAY_FRAME_BUFFER_PATH=/dev/fb2
DISPLAY_ERROR_COUNT_THRESHOLD=4

# Named Pipe Configurations
PIPE_FOLDER_PATH=${PROJECT_PATH}/app/pipes
TOUCH_SENSOR_TO_SCREEN_PIPE=${PIPE_FOLDER_PATH}/touch_sensor_to_screen_pipe
NFC_TO_SCREEN_PIPE=${PIPE_FOLDER_PATH}/nfc_to_screen_pipe

# Flag File Paths
PRE_REBOOT_FLAG=${PROJECT_PATH}/app/flags/pre_reboot_setup_done.flag
POST_REBOOT_FLAG=${PROJECT_PATH}/app/flags/post_reboot_setup_done.flag
REBOOT_HALTED_FLAG=${PROJECT_PATH}/app/flags/reboot_halted.flag
OVERLAY_MERGED_FLAG=${PROJECT_PATH}/app/flags/overlay_merged.flag

# Status Messages
OK_MSG="\033[0;32m[OK]     \033[0m"
WARNING_MSG="\033[0;33m[WARNING]\033[0m"
FAIL_MSG="\033[0;31m[FAIL]   \033[0m"