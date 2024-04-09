#!/bin/bash

CWD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CWD

source "${CWD}/../globals.sh"

function connect_network() {
  declare ssid pwd

  read -rp "SSID: " ssid
  read -rps "Password: " pwd
  nmcli device wifi connect "${ssid}" password "${pwd}"
  return $?
}

function pull_latest_changes() {
  if ! git pull origin $1; then
    return 1
  fi
  
  return 0
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

  echo "Pulling latest changes from ${branch}..."
  if ! pull_latest_changes "${branch}"; then
    echo "${FAIL}${RED}Unable to pull changes from '${branch}'${RESET}"
    return 1
  fi
  echo "${OK}${GREEN}Pulled all changes from '${branch}'.${RESET}"
  echo

  return 0
}

main
