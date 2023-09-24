#!/bin/bash

# Create a directory for application files.
sudo mkdir /var/lib/screen
# Change ownership of the directory to the current user.
sudo chown $USER:$USER /var/lib/screen
# Create two JSON files in the directory.
touch /var/lib/screen/batched_button_presses.json
touch /var/lib/screen/last_tags_and_ids.json
# Change ownership of the JSON files to the current user.
sudo chown $USER:$USER /var/lib/screen/batched_button_presses.json
sudo chown $USER:$USER /var/lib/screen/last_tags_and_ids.json

# Check if a command-line argument (driver name) is provided.
if [ -z "$1" ]
then
  echo "Please provide the driver name as a command-line argument."
  exit 1
fi

# Check if the NFC_Tracking directory exists in the user's home directory.
if [ -d "$HOME/NFC_Tracking" ]; then
    cd $HOME/NFC_Tracking
else
    echo "Directory $HOME/NFC_Tracking does not exist."
    exit 1
fi

# Create a logrotate configuration if it doesn't exist.
if [ ! -f "/etc/logrotate.d/programs" ]; then
    # Define the log rotation settings for the programs.log file.
    cat << EOF | sudo tee /etc/logrotate.d/programs
/var/log/programs.log {
    rotate 7
    daily
    compress
    missingok
    notifempty
    minsize 100M
    create 0664 potato root
    postrotate
        /bin/kill -HUP \`cat /var/run/read_ultralight.pid 2>/dev/null\` 2>/dev/null || true
    endscript
}
EOF
fi

# Create a systemd service file if it doesn't exist.
if [ ! -f "/etc/systemd/system/monitor.service" ]; then
    # Define the systemd service settings for the monitor service.
    cat << EOF | sudo tee /etc/systemd/system/monitor.service
[Unit]
Description=Monitor and restart C program

[Service]
Type=simple
ExecStart=/home/potato/NFC_Tracking/monitor.sh
User=root
Group=root
Environment=PATH=/usr/bin:/usr/local/bin
WorkingDirectory=/home/potato/NFC_Tracking
PIDFile=/var/run/read_ultralight.pid
ExecStop=/bin/kill -15 \$MAINPID
TimeoutSec=90
Restart=always

[Install]
WantedBy=multi-user.target
EOF
fi

# Reload the systemd manager configuration.
sudo systemctl daemon-reload

# Enable the monitor service and NetworkManager service.
sudo systemctl enable monitor.service
sudo systemctl enable NetworkManager

# Install packages from requirements.txt if it exists.
if [ -f "/home/potato/NFC_Tracking/requirements.txt" ]; then
    packages=$(cat $HOME/NFC_Tracking/requirements.txt)
    apt-get install -y $packages
fi

# Install Python packages using pip.
pip3 install boto3 netifaces

# Execute scripts to compile all programs and update permissions.
sudo sh compile_all.sh
sudo sh update_permissions.sh

# Get the driver name from the command-line argument.
driver=$1

# Update the system's package list.
sudo apt update

# Install the specified USB Wifi Adapter Driver.
cd $HOME
if [ "$driver" = "wn725n" ]
then
  # Install the TL-WN725N driver.
  if [ ! -d "TL-WN725N-TP-Link-Debian" ]; then
    git clone https://github.com/ilnanny/TL-WN725N-TP-Link-Debian.git
  fi
  sudo apt-get -y install build-essential linux-headers-$(uname -r)
  cd TL-WN725N-TP-Link-Debian
  make all
  make install
  insmod 8188eu.ko
elif [ "$driver" = "ac600" ]
then
  # Install the AC600 driver.
  if [ ! -d "rtl8812au" ]; then
    git clone https://github.com/aircrack-ng/rtl8812au.git
    sudo apt install -y dkms git build-essential libelf-dev
    cd rtl8812au/
    sudo make dkms_install
  fi
else
  echo "Invalid driver name. Please provide either 'wn725n' or 'ac600' as the command-line argument."
  exit 1
fi

# Install the libnfc library.
cd $HOME
git clone https://github.com/nfc-tools/libnfc.git
cd libnfc
autoreconf -vis
./configure --with-drivers=pn532_uart --prefix=/usr --sysconfdir=/etc
make
make install all

# Update the libnfc configuration file.
sudo cp contrib/udev/93-pn53x.rules /lib/udev/rules.d/
sudo mkdir -p /etc/nfc
sudo cp libnfc.conf.sample /etc/nfc/libnfc.conf
FILE="/etc/nfc/libnfc.conf"
CONN_STRING="pn532_uart:/dev/ttyAML6"
DEVICE_NAME="PN532_UART"
sudo sed -i "/^#.*device.connstring/c\\device.connstring = \"$CONN_STRING\"" $FILE
sudo sed -i "/^#.*device.name/c\\device.name = \"$DEVICE_NAME\"" $FILE

# Install the libre wiring tool.
cd $HOME
git clone https://github.com/libre-computer-project/libretech-wiring-tool.git
cd libretech-wiring-tool
cp $HOME/NFC_Tracking/spicc-ili9341-new.dts $HOME/libretech-wiring-tool/libre-computer/aml-s905x-cc/dt/
sudo ./install.sh

# Set the wiring overlay.
sudo ./ldto merge uart-a spicc spicc-ili9341-new