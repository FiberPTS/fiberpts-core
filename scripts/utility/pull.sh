#!/bin/sh

# Navigate to the user's home directory.
cd $HOME

# Check if the "NFC_Tracking" directory exists.
if [ -d "NFC_Tracking" ]; then
    # If it exists, navigate into the directory.
    cd NFC_Tracking
    # Fetch all updates from the remote repository.
    git fetch --all
    # Reset the local branch to match the state of the remote main branch.
    # This discards local changes in favor of the latest version from the remote repository.
    git reset --hard origin/main
else
    # If the directory doesn't exist, clone the NFC_Tracking repository from GitHub.
    git clone https://github.com/NxFerrara/NFC_Tracking.git
    # Navigate into the newly cloned directory.
    cd NFC_Tracking
fi