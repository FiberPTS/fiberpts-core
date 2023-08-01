#!/bin/sh
cd /home/potato
if [ -d "NFC_Tracking" ]; then
    cd NFC_Tracking
    git pull
else
    git clone https://github.com/NxFerrara/NFC_Tracking.git
    cd NFC_Tracking
fi
