#!/bin/bash

set -e

function assert_conditions() {
  # Root check
  if [ "$(id -u)" -ne 0 ]; then
    echo "${WARNING} This script must be run as root. Please use sudo."
    exit 1
  fi

  if [ -z "${PROJECT_DIR}" ]; then
    echo "${WARNING} Required environment variable PROJECT_DIR is not set."
    exit 1
  fi
}

function install_rtl8812au_driver() {
  local repo_url="https://github.com/aircrack-ng/rtl8812au.git"
  local version="v5.6.4.2"
  readonly repo_url version

  if [ ! -d "${PROJECT_DIR}/rtl8812au" ]; then
    echo "Installing rtl8812au driver..."
    git clone -b "${version}" "${repo_url}" "${PROJECT_DIR}/rtl8812au" > /dev/null
    make -C "${PROJECT_DIR}/rtl8812au" dkms_install > /dev/null
  else
    echo "Driver already installed."
  fi
}

function main() {
  assert_conditions
  install_rtl8812au_driver
}

main
