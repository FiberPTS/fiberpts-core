#!/bin/bash

CWD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CWD

set +a
source "${CWD}"/../globals.sh || return 1
source "${CWD}"/../paths.sh || return 1
set -a

function connect_network() {
  declare ssid pwd

  read -rp "SSID: " ssid
  read -rsp "Password: " pwd
  nmcli device wifi connect "${ssid}" password "${pwd}"
  return $?
}

function pull_latest_changes() {
  echo "Pulling latest changes from $1..."

  if ! git pull origin "$1"; then
    echo "${FAIL}${RED}Unable to pull changes from '$1'${RESET}"
    return 1
  fi
  
  return 0
}

function update_services() {
  echo "Updating service files..."

  for template in "${CWD}"/../../templates/*.service; do
    declare -r servname=$(basename "${template}")
    declare -r oldserv="${SYSTEM_DIR}/${servname}"
    declare -r newserv="${CWD}/${servname}.tmp"
    
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

function restart_services() {
  # Apply changes
  if ! systemctl daemon-reload; then
    echo "${FAIL} ${RED}Unable to reload the daemon.${RESET}"
    return 1
  fi

  for template in "${CWD}"/../../templates/*.service; do
    declare -r servname=$(basename "${template}")
    declare -r service="${SYSTEM_DIR}/${servname}"
    if ! systemctl restart "${servname}"; then
      echo "${FAIL} ${RED}Unable to restart '${servname}'.${RESET}"
      return 2
    fi
  done

  return 0
}

function check_system_status() {
  echo "Checking system status..."

  for template in "${CWD}"/../../templates/*.service; do
    declare -r servname=$(basename "${template}")
    
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

function rollback_changes() {
  echo "${WARNING} ${YELLOW}Rolling back changes...${RESET}"

  git reset --hard HEAD~1
  return "$(update_services)"
}

function main() {
  if wget -q --spider "https://google.com"; then
    echo "${OK}${GREEN}Network connection successful.${RESET}"
  else
    echo "${WARNING}${YELLOW}Network connection failed.${RESET}"

    declare response
    while true; do
      read -rp "Do you wish to connect to WiFi? [Y/n] " response
      case "${response}" in
        [Yy])
          break;
          ;;
        [Nn])
          return 1;
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
        echo "${OK}${GREEN}Network connection successful.${RESET}"
        break
      fi
      echo -e "Retrying...\n"
    done

    if ((attempt > max_attempts)); then
      echo "${FAIL}${RED}Network connection failed: Max retry attempts reached.${RESET}"
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
