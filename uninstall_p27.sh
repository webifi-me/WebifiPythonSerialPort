#!/bin/bash
# check if sudo is used
if [ "$(id -u)" != 0 ]; then
  echo 'Sorry, you need to run this script with sudo'
  exit 1
fi

# Create a log file for the uninstall as well as displaying the build on the tty as it runs
exec > >(tee build-webifiSerialPort.log)
exec 2>&1

systemctl stop webifiserialport.service
systemctl disable webifiserialport.service

rm /lib/systemd/system/webifiserialport.service
rm /etc/webifiserialport.ini
#rm /usr/sbin/Webifi_p27.py
rm /usr/sbin/WebifiPythonSerialPort_p27.py

systemctl daemon-reload
systemctl reset-failed
