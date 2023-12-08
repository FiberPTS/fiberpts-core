#!/bin/bash

# Path to the project directory
PROJECT_DIR="/opt/FiberPTS"

# Path to the virtual environment
VENV_DIR="$PROJECT_DIR/venv"

# Name of the .pth file
PTH_FILE_NAME="fiberpts.pth"

# Full path to the .pth file in the virtual environment
PTH_FILE_PATH="$VENV_DIR/lib/python3.11/site-packages/$PTH_FILE_NAME"

# Check if the virtual environment directory exists
if [ -d "$VENV_DIR" ]; then
    # Create or overwrite the .pth file with the project directory path
    echo "$PROJECT_DIR" > "$PTH_FILE_PATH"
    echo "Path added to $PTH_FILE_PATH"
else
    echo "Error: Virtual environment directory not found."
fi