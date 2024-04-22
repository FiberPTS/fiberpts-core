#!/bin/bash
#
# This script installs necessary Unix and Python packages (listed in
# requirements.txt).

set -e

#######################################
# Checks if the required PROJECT_PATH environment variable is set,
# and if the virtual environment directory exists.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Error messages to stdout and exits with status 1 on failure.
#######################################
function assert_variables() {
  # Verifies PROJECT_PATH is set
  if [ -z "${PROJECT_PATH}" ]; then
    echo "${WARNING} Required environment variable PROJECT_PATH is not set."
    exit 1
  fi

  if [ ! -d "${PROJECT_PATH}/venv" ]; then
    echo "${WARNING} Virtual environment not found at ${PROJECT_PATH}/venv. Please create it before running this script."
    exit 1
  fi
}

#######################################
# Installs Python packages listed in the requirements.txt file within the
# virtual environment.
# Globals:
#   PROJECT_PATH - Path to the project directory.
# Arguments:
#   None
# Outputs:
#   Status messages about Python package installation or error if
#   requirements.txt is missing.
#######################################
function install_python_packages() {
  local requirements="${PROJECT_PATH}/requirements.txt"
  readonly requirements

  if [ -f "${requirements}" ]; then
    echo "Installing Python packages..."
    # TODO: Add a spinner 
    "${PROJECT_PATH}/venv/bin/pip3" install -r "${requirements}" > /dev/null
  else
    echo "${WARNING} Python requirements file not found: ${requirements}"
    exit 1
  fi
}

#######################################
# Installs Unix packages required by the project.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
#######################################
function install_unix_packages() {
  # Required for parsing JSON when extracting first device ID from Supabase
  echo "Installing Unix packages..."
  apt-get install jq autoconf libtool -y > /dev/null
}

#######################################
# Installs c packages required by the project.
# Globals:
#   PROJECT_DIR - Directory of the project folder
#   PROJECT_PATH - Path of the project folder
# Arguments:
#   None
# Outputs:
#   None
#######################################
function install_c_packages() {
  echo "Installing C packages..."
  # Install libnfc
  if [ ! -d "${PROJECT_DIR}/libnfc" ]; then
    git clone "https://github.com/nfc-tools/libnfc.git" "${PROJECT_DIR}/libnfc" > /dev/null
    cd "${PROJECT_DIR}/libnfc"
    autoreconf -is > /dev/null 2>&1
    ./configure --with-drivers=pn532_uart --prefix=/usr --sysconfdir=/etc > /dev/null
    make install > /dev/null
    cp contrib/udev/93-pn53x.rules /lib/udev/rules.d/
    mkdir -p /etc/nfc
    echo -e "device.name = \"PN532_UART\"\ndevice.connstring = \"pn532_uart:/dev/ttyAML6\"" > "/etc/nfc/libnfc.conf"
    # Compile nfc_lib.c
    make -C "${PROJECT_PATH}/src/nfc_reader" > /dev/null
  fi
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
  install_unix_packages
  install_python_packages
  install_c_packages
}

main
