#!/bin/sh

# Navigate to the NFC_Tracking directory and pull the latest changes from the remote repository.
sh $HOME/NFC_Tracking/pull.sh

# Update the execute permissions for shell and Python scripts in the NFC_Tracking directory.
sh $HOME/NFC_Tracking/update_permissions.sh