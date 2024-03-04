#!/bin/bash

source ${PROJECT_PATH}/config/scripts_config.sh
# This tells the shell to exit the script if any command within the script exits with a non-zero status
set -e

# Setup logrotate config file
touch ${LOGROTATE_PATH}/${LOGCONF_FILENAME}
envsubst < ${PROJECT_PATH}/templates/${LOGCONF_FILENAME} > ${LOGROTATE_PATH}/${LOGCONF_FILENAME}

# Empty log file is required by the logrotate tool
touch ${PROJECT_PATH}/.app/logs/${LOG_FILENAME}