#!/bin/bash
#
# This script sets up the Python environment for the system. It creates a
# Python virtual environment, and adding the project path to a .pth file to
# facilitate module import. It requires the PROJECT_PATH environment variable
# to be set to the project's root directory.

set -e

#######################################
# Verifies that the required PROJECT_PATH environment variable is set.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Writes warning to stdout and exits with status 1 on failure.
#######################################
function assert_variables() {
  # Checks if PROJECT_PATH is set.
  if [ -z "${PROJECT_PATH}" ]; then
    echo "${WARNING} Required environment variable PROJECT_PATH is not set."
    exit 1
  fi
}

#######################################
# Creates a Python virtual environment in the project path if it does not
# already exist.
# Globals:
#   PROJECT_PATH - Path to the project directory.
# Arguments:
#   None
# Outputs:
#   Status message about virtual environment creation.
#######################################
function create_virtual_environment() {
  if [ ! -d "${PROJECT_PATH}/venv" ]; then
    # Installs necessary packages for virtual environment creation.
    apt install python3.11-venv python3-pip -y > /dev/null
    # Creates the virtual environment.
    python3 -m venv "${PROJECT_PATH}/venv" > /dev/null
    echo "${OK} Virtual environment created at '${PROJECT_PATH}/venv'"
  fi
}

#######################################
# Adds the project path to a .pth file within the virtual environment to
# allow for implicit module import. This is a workaround for importing
# modules without directly modifying service files.
# Globals:
#   PROJECT_PATH - Path to the project directory.
# Arguments:
#   None
# Outputs:
#   Status message about adding path to .pth file or error if venv not found.
#######################################
function add_path_to_pth() {
  # TODO: Fix implicit importing of FiberPTS modules without needing .pth file
  # by sourcing in service files
  local venv_dir="${PROJECT_PATH}/venv"
  local pth_file_name="fiberpts.pth"
  local pth_file_path="${venv_dir}/lib/python3.11/site-packages/${pth_file_name}"

  if [ -d "${venv_dir}" ]; then
    echo "${PROJECT_PATH}" > "${pth_file_path}"
    echo "${OK} Path added to ${pth_file_path}"
  else
    echo "${FAIL} Virtual environment directory not found."
    exit 1
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
  create_virtual_environment
  add_path_to_pth
}

main
