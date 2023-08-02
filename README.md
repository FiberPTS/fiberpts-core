Logs: /var/log/read_ultralight.log.*
Logrotate: /etc/logrotate.d/read_ultralight
Program Service: /etc/systemd/system/monitor.service
Source: /home/potato/NFC_Tracking

Must run commands on setup:
username: potato
password: ...
sudo systemctl enable ssh
sudo systemctl start ssh