#!/bin/bash

set -e
  
readonly TEMPLATES_DIR="${PROJECT_PATH}/templates"

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

function main() {
  assert_conditions
  process_service_files
}
