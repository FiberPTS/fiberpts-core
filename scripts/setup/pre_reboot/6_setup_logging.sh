#!/bin/bash

source ${PROJECT_PATH}/scripts/paths.sh

touch ${LOGROTATE_PATH}/${LOGCONF_FILENAME}
envsubst < ${PROJECT_PATH}/templates/${LOGCONF_FILENAME} > ${LOGROTATE_PATH}/${LOGCONF_FILENAME}

# Empty log file is required by the logrotate tool
touch ${PROJECT_PATH}/.app/logs/${LOG_FILENAME}