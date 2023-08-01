#!/bin/sh
cd /home/potato
if [ -d "NFC_Tracking" ]; then
    cd NFC_Tracking
    git fetch --all
    git reset --hard origin/master
else
    git clone https://github.com/NxFerrara/NFC_Tracking.git
    cd NFC_Tracking
fi