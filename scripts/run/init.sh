#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source "$SCRIPT_DIR/../../.env.shared"

# Map the console to the framebuffer
con2fbmap 1 2
# Wait for a moment
sleep 0.5
# Unmap the console
con2fbmap 1 0
# Clear the screen
dd if=/dev/zero of="$DISPLAY_FRAME_BUFFER_PATH" bs=1 count=153600