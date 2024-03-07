#!/bin/bash
#
# This script manages the installation and configuration of the
# libretech-wiring-tool, including setting custom device tree sources (DTS),
# managing overlay files, and ensuring the script is run with necessary
# privileges and environment variables.

set -e

#######################################
# Checks if the script is run as root and verifies that all required
# environment variables are set. Exits if any condition is not met.
# Globals:
#   PROJECT_DIR
#   PROJECT_PATH
#   OVERLAY_MERGED_FLAG
# Arguments:
#   None
# Outputs:
#   Writes warning to stdout and exits with status 1 on failure.
#######################################
function assert_conditions() {
  # Root check
  if [ "$(id -u)" -ne 0 ]; then
    echo "${WARNING} This script must be run as root. Please use sudo."
    exit 1
  fi

  if [ -z "${PROJECT_DIR}" ] || [ -z "${PROJECT_PATH}" ] || [ -z "${OVERLAY_MERGED_FLAG}" ]; then
    echo "${WARNING} Required environment variables PROJECT_DIR, PROJECT_PATH, and OVERLAY_MERGED_FLAG are not all set."
    exit 1
  fi
}

#######################################
# Copies the custom device tree source file to the destination directory.
# Globals:
#   PROJECT_PATH
#   PROJECT_DIR
# Arguments:
#   None
# Outputs:
#   None
#######################################
function set_custom_dts() {
  local source="${PROJECT_PATH}/custom/spi-cc-1cs-ili9341.dts"
  local dest="${PROJECT_DIR}/libretech-wiring-tool/libre-computer/aml-s905x-cc/dt"
  cp "${source} ${dest}"
}

#######################################
# Prompts the user to reset the overlays and performs the reset operation if 
# confirmed.
# Globals:
#   OVERLAY_MERGED_FLAG
# Arguments:
#   None
# Outputs:
#   User prompts and status messages regarding overlay reset.
#######################################
function reset_overlays() {
  while true; do
    read -p "Do you want to reset the overlays [Y/n] ?" answer
    echo

    case "${answer}" in
      [Yy])
        echo "Resetting overlays..."
        rm -f "${OVERLAY_MERGED_FLAG}"
        /opt/libretech-wiring-tool/ldto reset > /dev/null
        echo "Overlays reset. Reboot to apply changes."
        break
        ;;
      [Nn])
        echo "Overlays not reset."
        break
        ;;
      *)
        echo "Invalid input. Please answer 'Y' (yes) or 'n' (no)."
        ;;
    esac
  done
}

#######################################
# Prompts the user to merge overlays and performs the merge if confirmed.
# Globals:
#   OVERLAY_MERGED_FLAG
# Arguments:
#   None
# Outputs:
#   User prompts and status messages regarding overlay merge.
#######################################
function merge_overlays() {
  while true; do
    read -p "Do you want to merge the overlays [Y/n] ?" answer
    echo

    case "${answer}" in
      [Yy])
        echo "Merging overlays..."
        /opt/libretech-wiring-tool/ldto merge uart-a spi-cc-cs1 spi-cc-1cs-ili9341 > /dev/null
        echo "Overlays merged. Reboot to apply changes."
        touch "${OVERLAY_MERGED_FLAG}"
        break
        ;;
      [Nn])
        echo "Overlays not merged."
        break
        ;;
      *)
        echo "Invalid input. Please answer 'Y' (yes) or 'n' (no)"
        ;;
    esac
  done
}

#######################################
# Installs the libretech-wiring-tool if not already installed, sets custom DTS,
# and manages overlay files based on the overlay merged flag.
# Globals:
#   PROJECT_DIR
#   OVERLAY_MERGED_FLAG
# Arguments:
#   None
# Outputs:
#   Status messages regarding the installation and configuration of the tool.
#######################################
function install_libretech_wiring_tool() {
  local github_url=https://github.com/libre-computer-project/libretech-wiring-tool.git
  readonly github_url

  if [ ! -d "${PROJECT_DIR}/libretech-wiring-tool" ]; then
    echo "Installing libretech-wiring-tool..."
    git clone ${github_url} "${PROJECT_DIR}/libretech-wiring-tool" > /dev/null
    set_custom_dts
    bash "${PROJECT_DIR}/libretech-wiring-tool/install.sh" > /dev/null
    echo "${OK} Installed libretech-wiring-tool"
  else
    echo "${WARNING} Already installed libretech-wiring-tool."
  fi

  if [ -f "${OVERLAY_MERGED_FLAG}" ]; then
    reset_overlays
  else
    merge_overlays
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
  assert_conditions
  install_libretech_wiring_tool
}

main
