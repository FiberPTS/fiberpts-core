#!/bin/bash

set -e

# Setup logrotate config file
touch ${LOGROTATE_PATH}/${LOGCONF_FILENAME}
envsubst < ${PROJECT_PATH}/templates/${LOGCONF_FILENAME} > ${LOGROTATE_PATH}/${LOGCONF_FILENAME}

# Empty log file is required by the logrotate tool
touch ${PROJECT_PATH}/.app/logs/${LOG_FILENAME}