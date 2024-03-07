#!/bin/bash
#
# This script checks for necessary privileges and environment variables, then
# processes systemd service files from templates, enabling or updating services
# as needed.

set -e
  
readonly TEMPLATES_DIR="${PROJECT_PATH}/templates"

#######################################
# Verifies script is run as root and required environment variables are set.
# Globals:
#   PROJECT_PATH
#   SYSTEMD_DIR
# Arguments:
#   None
# Outputs:
#   Writes warnings to stdout and exits with status 1 on failure.
#######################################
function assert_conditions() {
  # Root check
  if [ "$(id -u)" -ne 0 ]; then
    echo "${WARNING} This script must be run as root. Please use sudo."
    exit 1
  fi

  if [ -z "${PROJECT_PATH}" ] || [ -z "${SYSTEMD_DIR}" ]; then
    echo "${WARNING} Required environment variables PROJECT_PATH or SYSTEMD_DIR are not set."
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

    # BUG: Service file is not created on line 26
    if [ ! -f "${SYSTEMD_DIR}/${service_filename}" ]; then
      envsubst < "${template}" > "${SYSTEMD_DIR}/${service_filename}"
      systemctl enable "${service_filename}" > /dev/null

      if [ "$?" -eq 0 ]; then
        echo "${OK} '${service_filename}' enabled"
      else
        echo "${FAIL} Failed to enable '${service_filename}'"
      fi
    else
      envsubst < "${template}" > "${SYSTEMD_DIR}/${service_filename}"
      systemctl daemon-reload
      systemctl restart "${service_filename}"

      if [ "$?" -eq 0 ]; then
        echo "${OK} '${service_filename}' updated"
      else
        echo "${FAIL} Failed to update '${service_filename}'"
      fi
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
  assert_conditions
  process_service_files
}
