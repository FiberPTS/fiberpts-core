#!/bin/bash

# INSTALL PYTHON AND CREATE VIRTUAL ENVIRONMENT
sudo apt install python3-pip python3-venv -y
python3 -m venv /opt/FiberPTS/venv

# INSTALL DEPENDENCIES
sudo /opt/FiberPTS/venv/bin/pip3 install -r /opt/FiberPTS/requirements.txt


# SET PROJECT PATH
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