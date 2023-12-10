#!/bin/bash

# THIS NEEDS TO BE RUN AFTER WIFI DRIVER

nmcli dev wifi connect "YourSSID" password "YourPassword"

nmcli connection modify "YourSSID" connection.autoconnect yes