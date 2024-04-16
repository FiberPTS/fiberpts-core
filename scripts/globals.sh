#!/bin/bash

if [ -t 1 ] && [ -n "$(tput colors)" ]; then
  RED="$(tput setaf 1)"
  GREEN="$(tput setaf 2)"
  YELLOW="$(tput setaf 3)"
  BLUE="$(tput setaf 4)"
  MAGENTA="$(tput setaf 5)"
  CYAN="$(tput setaf 6)"
  WHITE="$(tput setaf 7)"
  BOLD="$(tput bold)"
  RESET="$(tput sgr0)"
else
  RED=""
  GREEN=""
  YELLOW=""
  BLUE=""
  MAGENTA=""
  CYAN=""
  WHITE=""
  BOLD=""
  RESET=""
fi
export RED GREEN YELLOW BLUE MAGENTA CYAN WHITE BOLD RESET

# Status Messages
readonly OK="${GREEN}[OK]     ${RESET}"
readonly WARNING="${YELLOW}[WARNING]${RESET}"
readonly FAIL="${RED}[FAIL]   ${RESET}"
readonly CRITICAL="${BOLD}${RED}[CRITICAL]${RESET}"

# ensure_wifi_connection.sh
readonly CHECK_INTERVAL=30

# shutdown.sh
readonly SHUTDOWN_TIME="19:00:00"

# setup.sh
readonly TIMEZONE="America/New_York"