#!/bin/bash

set -e

assert_conditions() {
  # Root check
  if [ "$(id -u)" -ne 0 ]; then
    echo "${WARNING} This script must be run as root. Please use sudo."
    exit 1
  fi

  if [ -z "${PROJECT_PATH}" ]; then
    echo "${WARNING} Required environment variable PROJECT_PATH is not set."
    exit 1
  fi

  if [ ! -d "${PROJECT_PATH}/venv" ]; then
    echo "${WARNING} Virtual environment not found at ${PROJECT_PATH}/venv. Please create it before running this script."
    exit 1
  fi
}

install_python_packages() {
  local requirements="${PROJECT_PATH}/requirements.txt"
  readonly requirements

  if [ -f "${requirements}" ]; then
    echo "Installing Python packages..."
    "${PROJECT_PATH}/venv/bin/pip3" install -r "${requirements}" > /dev/null
  else
    echo "${WARNING} Python requirements file not found: ${requirements}"
    exit 1
  fi
}

install_unix_packages() {
  # Required for parsing JSON when extracting first device ID from Supabase
  apt-get install jq -y > /dev/null
}

main() {
  assert_conditions
  install_unix_packages
  install_python_packages
}

main
