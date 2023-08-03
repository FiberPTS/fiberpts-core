Logs: /var/log/read_ultralight.log.*
Logrotate: /etc/logrotate.d/read_ultralight
Program Service: /etc/systemd/system/monitor.service
Source: /home/potato/NFC_Tracking
LIBNFC: /home/potato/libnfc
Permission File: /lib/udev/rules.d/
Config File: /etc/nfc/libnfc.conf

Must run commands on setup:
Linux:
username: potato
password: ...
sudo systemctl enable ssh
sudo systemctl start ssh
Windows:
python setup_board.py --ip IP --usr USERNAME --pw PASSWORD --driver AC600
Linux:
python send_command.py --ip IP --command "nmcli device wifi connect WIFINAME password PASSWORD"