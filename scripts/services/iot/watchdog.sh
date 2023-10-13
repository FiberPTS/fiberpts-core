#!/bin/bash

# --- Constants ---
LOCKFILE="/var/run/watchdog.lock"
BASE_DIR="/home/potato/FiberPTS/src/iot"
PROGRAM_NAMES=("nfc_tap_listener" "action_tap_listener" "tap_event_handler.py")
declare -A PROGRAM_PIDS

# --- Function Definitions ---

# Acquire the main lock for this script
acquire_lock() {
  echo "Attempting to acquire main lock..."
  if (set -o noclobber; echo "$$" > "$LOCKFILE") 2>/dev/null; then
    trap 'rm -f "$LOCKFILE"' INT TERM EXIT
    echo "Main lock acquired."
  else
    echo "Failed to acquire main lock. Exiting."
    exit 1
  fi
}

# Initialize PIDs for the monitored programs
initialize_pids() {
  echo "Initializing program PIDs..."
  for program in "${PROGRAM_NAMES[@]}"; do
    PROGRAM_PIDS["$program"]="/var/run/${program%.py}.pid"
  done
  echo "Program PIDs initialized."
}

# Update permissions of the programs to make them executable
update_permissions() {
  echo "Updating permissions..."
  for program in "${PROGRAM_NAMES[@]}"; do
    sudo chmod +x "${BASE_DIR}/${program}"
  done
  echo "Permissions updated."
}

# Function to check and manage a given program
check_program() {
  local program=$1
  local lock_file="/var/run/${program%.py}.lock"
  echo "Checking program ${program}..."

  if (set -o noclobber; echo "$$" > "${lock_file}") 2>/dev/null; then
    local pid=$(pidof -x "${program}")
    echo "Lock acquired for ${program}."

    if [[ $pid ]]; then
      echo "Program ${program} is already running."
      echo $pid > "${PROGRAM_PIDS[${program}]}"
    else
      echo "Starting program ${program}."
      "${BASE_DIR}/${program}" >> /var/log/programs.log 2>&1 &
      echo $! > "${PROGRAM_PIDS[${program}]}"
    fi

    sudo rm -f "${lock_file}"
    echo "Lock released for ${program}."
  else
    echo "Failed to acquire lock for ${program}. Skipping."
  fi
}

# Function to terminate all monitored programs and remove lock files
on_sigterm() {
  echo "Received termination signal. Cleaning up..."
  for pid_file in "${PROGRAM_PIDS[@]}"; do
    if [[ -f "${pid_file}" ]]; then
      sudo kill "$(cat "${pid_file}")"
      sudo rm -f "${pid_file}"
      echo "Killed and removed PID file for program associated with ${pid_file}."
    fi
  done

  for program in "${PROGRAM_NAMES[@]}"; do
    local lock_file="/var/run/${program%.py}.lock"
    if [[ -f "${lock_file}" ]]; then
      sudo rm -f "${lock_file}"
      echo "Removed lock file ${lock_file}."
    fi
  done

  rm -f "$LOCKFILE"
  echo "Main lock file removed. Exiting."
  exit 0
}

# Function to check and manage WiFi connection
check_wifi() {
  echo "Checking WiFi connection..."
  if nmcli device wifi list | grep -q "FERRARAMFG"; then
    if ! nmcli con show --active | grep -q "FERRARAMFG"; then
      echo "Connecting to WiFi..."
      nmcli device wifi connect FERRARAMFG password FerraraWIFI1987
      nmcli con up FERRARAMFG
      echo "Connected to WiFi."
    else
      echo "Already connected to WiFi."
    fi
  else
    echo "Target WiFi not found."
  fi
}

# --- Main Execution ---
echo "Script starting..."
acquire_lock
initialize_pids
trap on_sigterm SIGTERM SIGINT SIGHUP SIGQUIT
export PYTHONPATH=$PYTHONPATH:/home/potato/.local/lib/python3.10/site-packages
update_permissions

echo "Entering main loop..."
while true; do
  check_wifi
  for program in "${PROGRAM_NAMES[@]}"; do
    check_program "${program}"
  done
  echo "Sleeping for 10 seconds..."
  sleep 10
done
