#!/bin/bash
#title           :init_gps.bash
#description     :the installation script for vehicle tracking using SocketIO and SIM HAT Nodule
#author          :Nicholas Putra Rihandoko
#date            :2023/06/21
#version         :2.1
#usage           :Modbus programming in Python
#notes           :
#==============================================================================

# Enable UART for communication with the RS485 Hat
sed -i 's/^enable_uart=0/enable_uart=1/g' /boot/firmware/config.txt
sed -i 's/^#enable_uart=0/enable_uart=1/' /boot/firmware/config.txt
sed -i 's/^#enable_uart=1/enable_uart=1/' /boot/firmware/config.txt
# If the previous lines does not exist yet, add it in /boot/firmware/config.txt
if ! sudo grep -q "enable_uart=1" /boot/firmware/config.txt; then
    sudo sed -i '4i enable_uart=1' /boot/firmware/config.txt
fi
# Use /dev/ttyAMA0 instead of /dev/ttyS0 to solve odd/even parity bit problem
if ! sudo grep -q "dtoverlay=disable-bt" /boot/firmware/config.txt; then
    sudo sed -i '4i dtoverlay=disable-bt' /boot/firmware/config.txt
fi
# Enable SPI
sudo raspi-config nonint do_spi 0
# Disable Serial Port to disable Serial Console, then enable Serial port without Serial Console
sudo raspi-config nonint do_serial 1
sudo raspi-config nonint do_serial 2
# Disable/comment bluetooth over serial port
sed -i 's/^dtoverlay=pi-minuart-bt/#&/g' /boot/firmware/config.txt
# ssh and VNC for remote access
if ! systemctl is-enabled --quiet ssh; then
  sudo systemctl enable ssh
  sudo systemctl start ssh
fi
if ! systemctl is-enabled --quiet vncserver-x11-serviced; then
  sudo raspi-config nonint do_vnc 0
fi

# Enable execute (run program) privilege for all related files
sudo chmod +x /home/$(logname)/NIW/gps_code/main__gps.py
sudo chmod +x /home/$(logname)/NIW/gps_code/gnss_config.py
sudo chmod +x /home/$(logname)/NIW/gps_code/dashboard_server/server.js

# Install pip for python library manager
sudo apt update
# Disable ModemManager while configuring the AT command
if systemctl list-unit-files | grep -qw ModemManager; then
  if systemctl is-active --quiet ModemManager; then
    sudo systemctl stop ModemManager
  fi
  if systemctl is-enabled --quiet ModemManager; then
    sudo systemctl disable ModemManager
  fi
fi
sudo apt install python3-pip -y
# Install the necessary python library
sudo apt install python3-socketio -y
sudo apt install python3-websocket -y
sudo apt install python3-pymysql -y
# 'zerotier' for virtual LAN and remote access
sudo apt install curl nmap -y
curl -s https://install.zerotier.com | sudo bash
# cron for task automation
sudo apt install cron -y
sudo systemctl enable cron

# Start GPS module configuration
while true; do
echo ""
read -p "Will this device act as GPS transciever? (Y/n) " yn_gps
case $yn_gps in
[Yy]*)
while true; do
echo ""
echo "The GPS module needs to be configured"
echo "Available configuration:"
echo "1) SIM7600"
echo "2) SE100"
echo "3) ~ others"
echo ""
read -p "Input the number --> " gps_model
case $gps_model in
[1]*)
sudo python3 /home/$(logname)/NIW/gps_code/gnss_config.py SIM7600
break;;
[2]*)
sudo python3 /home/$(logname)/NIW/gps_code/gnss_config.py SE100
break;;
[3]*)
echo ""
echo "Please configure the GPS module by yourself"
echo "Make sure you import the GNSS python script and"
echo "add the correct 'port_id' variable in the main__gps.py"
break;;
*)
echo ""
echo "Invalid input. Please answer from the number on the list.";;
esac
done
break;;
[Nn]*)
echo "OK"
break;;
*)
echo ""
echo "Invalid input.Try again.";;
esac
done

# Start GPS Dashboard configuration
while true; do
echo ""
read -p "Will this device act as dashboard server? (Y/n) " yn_dashboard
case $yn_dashboard in
[Yy]*)
# Install Node js, Express js, ans socket.io
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | sudo bash
source ~/.bashrc
nvm install 12.22.12
nvm alias default 12.22.12
sudo apt install npm -y
cd NIW/gps_code/dashboard_server
npm init -y
npm i socket.io@4.7.1 express@4.18.2 morgan@1.10.0 dotenv@16.3.1
npm audit fix
npm update engine.io ws
break;;
[Nn]*)
echo "OK"
break;;
*)
echo ""
echo "Invalid input. Try again.";;
esac
done
cd

# Enable ModemManager while after the AT command
#if systemctl list-unit-files | grep -qw ModemManager; then
#  if ! systemctl is-active --quiet ModemManager; then
#    sudo systemctl start ModemManager
#  fi
#  if ! systemctl is-enabled --quiet ModemManager; then
#    sudo systemctl enable ModemManager
#  fi
#fi

echo ""
echo "=========================================================="
echo ""
echo "Installation of GPS system is finished"
echo ""
echo "Please reboot the RaspberryPi, just in case :)"
echo ""
echo "=========================================================="
echo ""
exit 0