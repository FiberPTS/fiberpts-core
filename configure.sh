#!/bin/bash

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

# Install dependencies
while read p; do
  apt-get install -y $p;
done </home/potato/NFC_Tracking/requirements.txt

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