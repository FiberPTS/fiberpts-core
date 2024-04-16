#!/bin/bash
#
# This script automates the process of updating the FiberPTS system. It ensures
# network connectivity, pulls the latest changes for a specified branch from the
# repository, updates service files based on the latest templates, restarts services,
# and checks the system status to confirm successful updates. If necessary, it can
# also rollback changes in case of update failure.

readonly CWD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set +a
source "${CWD}"/../globals.sh || return 1
source "${CWD}"/../paths.sh || return 1
set -a

#######################################
# Ensures the script is run with root privileges, exiting with an error
# if it's not.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Error message to stdout and exits with status 1 if not run as root.
#######################################
function assert_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo -e "${WARNING} ${YELLOW}This script must be run as root. Please use sudo.${RESET}"
    exit 1
  fi
}

#######################################
# Connects to a WiFi network using NetworkManager CLI (nmcli).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Prompts user for SSID and password. Outputs nmcli command results.
#######################################
function connect_network() {
  declare ssid pwd

  read -rp "SSID: " ssid
  read -rsp "Password: " pwd
  nmcli device wifi connect "${ssid}" password "${pwd}"
  return $?
}

#######################################
# Pulls the latest changes from a specified Git branch.
# Globals:
#   FAIL, RED, RESET - Used for coloring the error message.
# Arguments:
#   $1 - The name of the branch to pull changes from.
# Outputs:
#   Status messages regarding the pull operation.
#######################################
function pull_latest_changes() {
  echo "Pulling latest changes from $1..."

  if ! git -C "${PROJECT_PATH}" pull origin "$1"; then
    echo "${FAIL}${RED}Unable to pull changes from '$1'${RESET}"
    return 1
  fi
  
  return 0
}

#######################################
# Updates service files based on templates. It replaces the existing
# service files with new ones generated from templates if there are changes.
# Globals:
#   CWD, SYSTEM_DIR - Directories for templates and system services.
# Arguments:
#   None
# Outputs:
#   Status messages regarding the updates of service files.
# Returns:
#   Status of restart_services function.
#######################################
function update_services() {
  echo "Updating service files..."

  for template in "${CWD}"/../../templates/*.service; do
    declare servname=$(basename "${template}")
    declare oldserv="${SYSTEMD_DIR}/${servname}"
    declare newserv="${CWD}/${servname}.tmp"
    
    envsubst < "${template}" > "${newserv}"
    if ! diff "${newserv}" "${oldserv}"; then
      if cp "${newserv}" "${oldserv}"; then
        echo "'${servname}' updated"
      fi
    fi
    rm "${newserv}"
  done

  return "$(restart_services)"
}

#######################################
# Reloads the systemd daemon and restarts all services defined in the 
# `templates` directory.
# Globals:
#   CWD, SYSTEM_DIR - Directories for service templates and system services.
# Arguments:
#   None
# Outputs:
#   Status messages regarding daemon reload and service restarts.
#######################################
function restart_services() {
  # Apply changes
  if ! systemctl daemon-reload; then
    echo "${FAIL} ${RED}Unable to reload the daemon.${RESET}"
    return 1
  fi

  for template in "${CWD}"/../../templates/*.service; do
    declare servname=$(basename "${template}")
    if ! systemctl restart "${servname}"; then
      echo "${FAIL} ${RED}Unable to restart '${servname}'.${RESET}"
      return 2
    fi
  done

  return 0
}

#######################################
# Checks the status of all services defined in the `templates` directory.
# If a service is not active, attempts to start it.
# Globals:
#   CWD - Directory containing service templates.
# Arguments:
#   None
# Outputs:
#   Status messages regarding the activity of each service and attempts to
#   start inactive services.
#######################################
function check_system_status() {
  echo "Checking system status..."

  for template in "${CWD}"/../../templates/*.service; do
    declare servname=$(basename "${template}")
    
    status=$(systemctl is-active "${servname}")
    if [ "${status}" != "active" ]; then
      echo "${WARNING} ${YELLOW}'${servname}' is not active.${RESET}"
      
      echo "Attempting to start..."
      systemctl start "${servname}"

      if ! systemctl is-active --quiet "${servname}"; then
        echo "${FAIL} ${RED}Unable to start '${servname}'${RESET}"
        rollback_changes || echo "${CRITICAL} ${RED}Unable to rollback changes!${RESET}" 
        return 1
      fi
    fi
    echo "${OK} '${servname}' is active."
  done

  return 0
}

#######################################
# Rolls back the most recent changes by resetting the HEAD to the previous
# commit and then restores the contents of the service files.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Warning message about rolling back changes and the results of updating
#   services after the rollback.
# Returns:
#   Status of update_services function.
#######################################
function rollback_changes() {
  echo "${WARNING} ${YELLOW}Rolling back changes...${RESET}"

  git reset --hard HEAD~1
  return "$(update_services)"
}

#######################################
# Main function to ensure network connectivity, pull latest changes from a
# specified branch, update service files, and check the system status. If
# the network is down, it attempts to connect to WiFi.
# Globals:
#   OK, GREEN, WARNING, YELLOW, FAIL, RED, RESET - Used for coloring messages.
# Arguments:
#   None
# Outputs:
#   Various status messages about network connectivity, Git operations, service
#   file updates, and system status checks.
#######################################
function main() {
  assert_root

  if wget -q --spider "https://google.com"; then
    echo "${OK} ${GREEN}Network connection successful.${RESET}"
  else
    echo "${WARNING} ${YELLOW}Network connection failed.${RESET}"

    declare response
    while true; do
      read -rp "Do you wish to connect to WiFi? [Y/n] " response
      case "${response}" in
        [Yy])
          break
          ;;
        [Nn])
          return 1
          ;;
        *)
          echo "Invalid input: Answer either 'y' (yes) or 'n' (no)."
          echo
          ;;
      esac
    done

    declare -r max_attempts=3
    for ((attempt = 1; attempt <= max_attempts; attempt++)); do
      echo "Attempt ${attempt} of ${max_attempts}:"
      if connect_network; then
        echo "${OK} ${GREEN}Network connection successful.${RESET}"
        break
      fi
      echo -e "Retrying...\n"
    done

    if ((attempt > max_attempts)); then
      echo "${FAIL} ${RED}Network connection failed: Max retry attempts reached.${RESET}"
      return 1
    fi
  fi
  echo

  declare branch;
  read -rp "Specify target branch (default: main): " branch
  if [ -z "${branch}" ]; then
    branch="main"
  fi

  pull_latest_changes "${branch}" || return 1
  echo -e "${OK}${GREEN}Pulled all changes from '${branch}'.${RESET}\n"

  update_services || return  # two kinds of errors can be reported through $?
  echo -e "${OK} ${GREEN}Updated all service files${RESET}\n"

  check_system_status || return 1
  echo -e "${BOLD}${OK} ${GREEN}Successful update. FiberPTS is up and running.${RESET}"

  return 0
}

main
