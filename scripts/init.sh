#!/bin/bash

# Initialize Display

# Map the console to the framebuffer
con2fbmap 1 2
# Wait for a moment
sleep 0.5
# Unmap the console
con2fbmap 1 0
# Clear the screen
dd if=/dev/zero of=/dev/fb2 bs=1 count=153600