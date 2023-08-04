Logs: /var/log/programs.log.*
Logrotate: /etc/logrotate.d/programs
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
python send_command.py --ip IP --usr USERNAME --pw PASSWORD --command "nmcli device wifi connect WIFINAME password PASSWORD"

To Do: 
- Running this in parallel
- May need to deal with installing gcc-8 for the wifi adapter driver
	- wget http://deb.debian.org/debian/pool/main/g/gcc-defaults/gcc_8.3.0-1_arm64.deb
