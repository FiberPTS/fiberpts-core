#!/bin/bash

# Add a application user
sudo adduser fiberpts

# Set application ownership
sudo chown -R fiberpts:fiberpts /opt/FiberPTS

# Set groups
sudo usermod -a -G video fiberpts

# Set executable access
find /opt/FiberPTS/scripts -type f -exec chmod +x {} \;
find /opt/FiberPTS/src -type f -exec chmod +x {} \;

# Set read access
chmod 444 /opt/FiberPTS/.env.shared
chmod 444 /opt/FiberPTS/requirements.txt

# Set read/write access
chmod -R 660 /opt/FiberPTS/app