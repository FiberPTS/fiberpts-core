#!/bin/bash

# Define log file path
LOG_DIR="/FiberPTS/logs"
LOG_FILE="RuntimeLogs.log"

# Define the maximum number of rotated logs to keep
MAX_ROTATIONS=4

# Define the maximum log file size in bytes (1 GB)
MAX_LOG_SIZE=$((1024*1024*1024))  # 1 GB in bytes

# Create the log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if the log file exists
if [ ! -f "$LOG_DIR/$LOG_FILE" ]; then
    touch "$LOG_DIR/$LOG_FILE"
fi

# Rotate logs
rotate_logs() {
    local log_file="$1"
    local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    local rotated_log="$log_file.$timestamp"

    # Move existing log files
    for ((i=$MAX_ROTATIONS; i>=1; i--)); do
        prev_index=$((i-1))
        prev_log="$log_file.$prev_index"
        current_log="$log_file.$i"

        if [ -f "$LOG_DIR/$prev_log" ]; then
            mv "$LOG_DIR/$prev_log" "$LOG_DIR/$current_log"
        fi
    done

    # Rotate current log file
    mv "$LOG_DIR/$log_file" "$LOG_DIR/$log_file.0"

    # Create new log file
    touch "$LOG_DIR/$log_file"
}

# Check log file size and rotate if it exceeds the threshold
check_log_size() {
    local log_file="$1"
    local log_size=$(du -b "$LOG_DIR/$log_file" | cut -f1)

    if [ "$log_size" -gt "$MAX_LOG_SIZE" ]; then
        rotate_logs "$log_file"
    fi
}

# Rotate logs every week or if size exceeds 1 GB
while true; do
    rotate_logs "$LOG_FILE"
    check_log_size "$LOG_FILE"
    sleep 7d  # Rotate logs every 7 days
done