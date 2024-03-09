#!/bin/bash
#
# This script checks for necessary privileges and environment variables, then
# processes systemd service files from templates, enabling or updating services
# as needed.

set -e
  
readonly TEMPLATES_DIR="${PROJECT_PATH}/templates"

#######################################
# Verifies required environment variables are set.
# Globals:
#   PROJECT_PATH
#   SYSTEMD_DIR
# Arguments:
#   None
# Outputs:
#   Writes warnings to stdout and exits with status 1 on failure.
#######################################
function assert_variables() {
  local missing_env_variables
  if [ -z "${PROJECT_PATH}" ]; then
    missing_env_variables+=("PROJECT_PATH")
  fi
  if [ -z "${SYSTEM_DIR}" ]; then
    missing_env_variables+=("SYSTEM_DIR")
  fi
  if [ ${#missing_env_variables[@]} -gt 0 ]; then
    echo "${WARNING} Required environment variables ${missing_env_variables[*]} are not set."
    exit 1
  fi
}

#######################################
# Processes .service templates, enabling new services or updating existing
# ones.
# Globals:
#   TEMPLATES_DIR
#   SYSTEMD_DIR
# Arguments:
#   None
# Outputs:
#   Status messages regarding service enabling or updating.
#######################################
function process_service_files() {
  for template in "${TEMPLATES_DIR}"/*.service; do
    local service_filename
    service_filename=$(basename "${template}")

    if [ ! -f "${SYSTEMD_DIR}/${service_filename}" ]; then
      envsubst < "${template}" > "${SYSTEMD_DIR}/${service_filename}"
      systemctl enable "${service_filename}" > /dev/null
      if [ "$?" -eq 0 ]; then
        echo "${OK} '${service_filename}' enabled"
      else
        echo "${FAIL} Failed to enable '${service_filename}'"
        exit 1
      fi
    else
      envsubst < "${template}" > "${SYSTEMD_DIR}/${service_filename}"
      systemctl daemon-reload
      if [ "$?" -ne 0 ]; then
        echo "${FAIL} Failed to reload systemd daemon"
        exit 1
      fi

      systemctl restart "${service_filename}"
      if [ "$?" -ne 0 ]; then
        echo "${FAIL} Failed to restart '${service_filename}'"
        exit 1
      fi

      echo "${OK} '${service_filename}' updated"
    fi
  done
}

#######################################
# Main function to orchestrate script execution.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None directly, but calls functions that produce outputs.
#######################################
function main() {
  assert_variables
  process_service_files
}
