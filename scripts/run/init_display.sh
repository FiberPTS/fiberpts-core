#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATHS="${SCRIPT_DIR}/../../scripts/paths.sh"
readonly SCRIPT_DIR PATHS

function init_display() {
  flock -x 200

  local fb_number="${DISPLAY_FRAME_BUFFER_PATH: -1}"

  # Map the console to the framebuffer
  con2fbmap 1 "${fb_number}"
  sleep 0.5

  # Unmap the console
  con2fbmap 1 0

  flock -u 200
}

function main() {
  source "${PATHS}"

  exec 200> "${DISPLAY_FRAME_BUFFER_LOCK_PATH}" 
  trap 'flock -u 200' EXIT

  if [ -e "${DISPLAY_FRAME_BUFFER_PATH}" ]; then
    init_display
  else
    echo -e "${WARNING} ${DISPLAY_FRAME_BUFFER_PATH} does not exist."
  fi
}

main
