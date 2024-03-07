#!/bin/bash
#
# Sets up log rotation for application logs using environment variables to
# configure paths and filenames.

set -e

# Replace environment variables in template and create logrotate config
envsubst < ${PROJECT_PATH}/templates/${LOGCONF_FILENAME} > ${LOGROTATE_PATH}/${LOGCONF_FILENAME}

# Empty log file is required by the logrotate tool
touch ${PROJECT_PATH}/.app/logs/${LOG_FILENAME}
