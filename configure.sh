#!/bin/bash
cd /home/potato/NFC_Tracking
# Create logrotate configuration
cat << EOF > /etc/logrotate.d/read_ultralight
/var/log/read_ultralight.log {
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

# Create systemd service file
cat << EOF > /etc/systemd/system/monitor.service
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

# Reload systemd manager configuration
systemctl daemon-reload

# Enable the service
systemctl enable monitor.service

# Clone the repository
git clone https://github.com/NxFerrara/NFC_Tracking.git /home/potato/NFC_Tracking

packages=$(cat /home/potato/NFC_Tracking/requirements.txt)
apt-get install -y $packages

sh compile_all.sh
sh update_permissions.sh

# Check if command-line argument is provided
if [ -z "$1" ]
then
  echo "Please provide the driver name as a command-line argument."
  exit 1
fi

driver=$1  # Get driver name from command-line argument

# Update and upgrade the system
sudo apt update
sudo apt upgrade -y

if [ "$driver" = "wn725n" ]
then
  git clone https://github.com/ilnanny/TL-WN725N-TP-Link-Debian.git
  cd rtl8188eu
  sudo apt-get -y install build-essential linux-headers-$(uname -r)
  cd TL-WN725N-TP-Link-Debian
  make all
  make install
  insmod 8188eu.ko
elif [ "$driver" = "ac600" ]
then
  # Install the ac600 driver
  sudo apt install -y dkms git build-essential libelf-dev
  git clone https://github.com/aircrack-ng/rtl8812au.git
  cd rtl8812au/
  sudo make dkms_install
else
  echo "Invalid driver name. Please provide either 'wn725n' or 'ac600' as the command-line argument."
  exit 1
fi

sudo reboot

# Parse command-line arguments
#while (( "$#" )); do
#  case "$1" in
#    --key)
#      if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
#        KEY=$2
#        shift 2
#      else
#        echo "Error: Argument for $1 is missing" >&2
#        exit 1
#      fi
#      ;;
#    -*|--*=) 
#      echo "Error: Unsupported flag $1" >&2
#      exit 1
#      ;;
#    *)
#      shift
#      ;;
#  esac
#done

# Use the key argument in the script
# Rest of the script remains the same except for the last part

# Update authorized_keys file
#mkdir -p /home/potato/.ssh
#echo "$KEY" >> /home/potato/.ssh/authorized_keys
#chmod 600 /home/potato/.ssh/authorized_keys