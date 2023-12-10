#!/bin/bash

# Load the environment variables from the .env.shared file
set -a  # automatically export all variables
PROJECT_DIR="/opt"
PROJECT_PATH="$PROJECT_DIR/FiberPTS"
source "$PROJECT_DIR/FiberPTS/.env.shared"
set +a  # stop automatically exporting
