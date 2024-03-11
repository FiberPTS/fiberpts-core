#!/bin/bash
#
# This script installs the rtl8812au driver from a specified version and
# repository URL if it's not already installed in the specified project
# directory.

set -e

#######################################
# Checks if the PROJECT_DIR environment variable is set, 
# exiting with an error if any condition is not met.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Writes warning to stdout and exits with status 1 on failure.
#######################################
function assert_variables() {
  # Checks if PROJECT_DIR is set.
  if [ -z "${PROJECT_DIR}" ]; then
    echo "${WARNING} Required environment variable PROJECT_DIR is not set."
    exit 1
  fi
  
}

#######################################
# Clones and installs the rtl8812au driver from a specified repository and
# version if it's not already installed in the PROJECT_DIR directory.
# Globals:
#   PROJECT_DIR - The directory where the rtl8812au driver is to be installed.
# Arguments:
#   None
# Outputs:
#   Status messages regarding the installation process.
#######################################
function install_rtl8812au_driver() {
  local repo_url="https://github.com/aircrack-ng/rtl8812au.git"
  local version="v5.6.4.2"
  readonly repo_url version

  if [ ! -d "${PROJECT_DIR}/rtl8812au" ]; then
    echo "Installing rtl8812au driver..."
    # TODO: Add spinner animation. 
    git clone -b "${version}" "${repo_url}" "${PROJECT_DIR}/rtl8812au" > /dev/null # TODO, same as in script 1 of pre_reboot
    make -C "${PROJECT_DIR}/rtl8812au" dkms_install > /dev/null
  else
    echo "${WARNING} Driver already installed."
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
  install_rtl8812au_driver
}

main
