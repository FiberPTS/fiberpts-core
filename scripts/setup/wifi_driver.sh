#!/bin/bash

sudo apt-get install git -y

cd /opt

git clone -b v5.6.4.2 https://github.com/aircrack-ng/rtl8812au.git

cd rtl8812au

sudo make dkms_install

