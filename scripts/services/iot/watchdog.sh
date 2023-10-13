#!/bin/bash

# Constants
LOCKFILE="/var/run/watchdog.lock"
BASE_DIR="/home/potato/FiberPTS/src/iot"
PROGRAM_NAMES=("nfc_tap_listener" "action_tap_listener" "tap_event_handler.py")
declare -A PROGRAM_PIDS

# Acquire main lock
acquire_lock() {
  if (set -o noclobber; echo "$$" > "$LOCKFILE") 2>/dev/null; then
    trap 'rm -f "$LOCKFILE"' INT TERM EXIT
  else
    echo "Failed to acquire lockfile: $LOCKFILE. Held by $(cat $LOCKFILE)"
    exit 1
  fi
}

# Initialize program PIDs
initialize_pids() {
  for program in "${PROGRAM_NAMES[@]}"; do
    PROGRAM_PIDS["$program"]="/var/run/${program%.py}.pid"
  done
}

# Update permissions to be executable
update_permissions() {
  for program in "${PROGRAM_NAMES[@]}"; do
    sudo chmod +x "${BASE_DIR}/${program}"
  done
}

# Check and start/stop a given program
check_program() {
  local program=$1
  local lock_file="/var/run/${program%.py}.lock"

  if (set -o noclobber; echo "$$" > "${lock_file}") 2>/dev/null; then
    local pid=$(pidof -x "${program}")

    if [[ $pid ]]; then
      echo $pid > "${PROGRAM_PIDS[${program}]}"
    else
      "${BASE_DIR}/${program}" >> /var/log/programs.log 2>&1 &
      echo $! > "${PROGRAM_PIDS[${program}]}"
    fi

    sudo rm -f "${lock_file}"
  fi
}

# Kill monitored programs on SIGTERM/SIGINT/SIGHUP/SIGQUIT
on_sigterm() {
  for pid_file in "${PROGRAM_PIDS[@]}"; do
    if [[ -f "${pid_file}" ]]; then
      sudo kill "$(cat "${pid_file}")"
      sudo rm -f "${pid_file}"
    fi
  done
  exit 0
}

# Check WiFi connection
check_wifi() {
  if nmcli device wifi list | grep -q "FERRARAMFG"; then
    if ! nmcli con show --active | grep -q "FERRARAMFG"; then
      nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
      nmcli con up FERRARAMFG
    fi
  fi
}

# Main
acquire_lock
initialize_pids
trap on_sigterm SIGTERM SIGINT SIGHUP SIGQUIT
export PYTHONPATH=$PYTHONPATH:/home/potato/.local/lib/python3.10/site-packages
update_permissions

while true; do
  check_wifi
  for program in "${PROGRAM_NAMES[@]}"; do
    check_program "${program}"
  done
  sleep 10
done