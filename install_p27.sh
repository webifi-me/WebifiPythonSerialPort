#!/bin/bash
# check if sudo is used
if [ "$(id -u)" != 0 ]; then
  echo 'Sorry, you need to run this script with sudo'
  exit 1
fi

# Create a log file of the build as well as displaying the build on the tty as it runs
exec > >(tee build-webifiSerialPort.log)
exec 2>&1

pip install websocket-client

# copy all the files to the correct folder
#yes | cp -rf ./Webifi_p27.py /usr/sbin/
yes | cp -rf ./WebifiPythonSerialPort_p27.py /usr/sbin/

echo -n "Enter your Webifi connect name and press [ENTER]: "
read connectname

echo -n "Enter your Webifi connect password and press [ENTER]: "
read password

echo -n "Enter your Webifi network name and press [ENTER]: "
read network

echo -n "Use encryption? 1 or 0 and press [ENTER]: "
read useEncryption

echo -n "Serial port name and press [ENTER] (Example: /dev/ttyUSB0): "
read serport

echo -n "Enter baudrate and press [ENTER] (Example: 115200): "
read baudrate

# create ini file
cat > /etc/webifiserialport.ini <<- EOM
# If you don't have the details for this section, please register on www.webifi.me and see our Getting started
# and How it works pages
[WebifiConnectionDetails]

# Connect name configured on www.webifi.me
connectname: $connectname

# Your connect password
password: $password

# Default networks names that this instance should be part of. For a serial port you normally only want
# to communicate over one network
network1: $network
#network2: home
#network3: office

# Use SSL/TLS encryption. Makes communication slightly slower but no one can see your data over the internet.
# This should be 1 if you use this for accessing a terminal on a linux device, otherwise passwords will be
# exchanged in clear text. Options are 1 or 0
encryption: $useEncryption

# Use websocket for connection. If 0 then long polling is used. Options are 1 or 0
useWebsocket: 1

# The data type sent with all data from this instance. This is handy if you have multiple devices on the same network
# and need the receiving device to easily differentiate where the data is coming from
datatype: serial

# If you would like to use logging then specify the directory that must be used to store log files. When enabled
# log entries will also be written to the console. Leave empty to disable logging
logDirectory:

[SerialPortSettings]

# Serial port used for communication
serport: $serport

# Parity used by serial port, options are N for None, O for Odd and E for Even
parity: N

# Baud rate used by serial port
baudrate: $baudrate

# Number of data bits used by serial port, options are 7 or 8
numbits: 8

# Stop bits used by serial port, options are 1 or 2
stopbits: 1
EOM

printf "\n\nThe settings are stored at /etc/webifiserialport.ini if you need to make any changes."
printf "\nIf you changed this file, restart the service by entering: sudo service webifiserialport restart"
printf "\n\n\n"

# create auto-start script
cat > /lib/systemd/system/webifiserialport.service <<- EOM
[Unit]
Description=Webifi Serial Port
After=multi-user.target

[Service]
Type=idle
ExecStart=/bin/sh -c '/usr/bin/python /usr/sbin/WebifiPythonSerialPort_p27.py /etc/webifiserialport.ini'

[Install]
WantedBy=multi-user.target
EOM

chmod 644 /lib/systemd/system/webifiserialport.service

systemctl daemon-reload
systemctl enable webifiserialport.service
systemctl start webifiserialport.service
