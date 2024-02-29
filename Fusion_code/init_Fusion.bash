#!/bin/bash
#title           :init_Fusion.bash
#description     :CAN/RS485 Hat & ADDA Hat module installation script
#author          :Nicholas Putra Rihandoko, Nauval Chantika
#date            :2024/02/05
#version         :2.2
#usage           :Data Monitoring in python
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

# Disable Serial Port to disable Serial Console, then enable Serial port without Serial Console
sudo raspi-config nonint do_serial 1
sudo raspi-config nonint do_serial 2

# Disable/comment bluetooth over serial port
sed -i 's/^dtoverlay=pi-minuart-bt/#&/g' /boot/firmware/config.txt

# Enable SPI interface to communicate with the CAN Hat
sudo raspi-config nonint do_spi 0

# Check whether the command line is already exist in /boot/firmware/config.txt
if ! sudo grep -q "dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000" /boot/firmware/config.txt; then
    # Append the file into /boot/config.txt to enable RaspberryPi handling of CAN device
    sudo echo "# Enable CAN controller on Waveshare RS485/CAN Hat" >> /boot/firmware/config.txt
    sudo echo "dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000" >> /boot/firmware/config.txt
fi

# ssh and VNC for remote access
if ! systemctl is-enabled --quiet ssh; then
  sudo systemctl enable --now ssh
fi
if ! systemctl is-enabled --quiet vncserver-x11-serviced; then
  sudo raspi-config nonint do_vnc 0
fi

# Install pip for python library manager
sudo apt update
sudo apt install can-utils -y
sudo apt install ttf-wqy-zenhei -y
sudo apt install python3-pip -y
# Install the necessary python library
# For wide-range use
sudo apt install python3-pymysql -y
sudo apt install python3-pymodbus -y
sudo apt install python3-can -y
sudo apt install python3-rpi.gpio -y
sudo apt install python3-spidev -y


# For Virtual Environment
#python3 -m venv myenv
#source myenv/bin/activate
#pip3 install pymysql pymodbus python-can  RPi.GPIO spidev
#deactivate

# 'zerotier' for virtual LAN and remote access
sudo apt install curl nmap -y
curl -s https://install.zerotier.com | sudo bash
# cron for task automation
sudo apt install cron -y
sudo systemctl enable cron

# Enable execute (run program) privilege for all related files
SCRIPT_PATH="/home/$(logname)/NIW/Fusion_code/main__Fusion.py"
sudo chmod +x $SCRIPT_PATH
sudo chmod 777 /home/$(logname)/NIW/Fusion_code/save/data_realtime_log.csv
sudo chmod 777 /home/$(logname)/NIW/Fusion_code/save/data_recap_log.csv

# To make the script run automatically everytime raspberry pi powered on
cat <<EOF > /etc/systemd/system/iot_niw.service
[Unit]
Description= NIW IOT MONITORING SYSTEM
After=multi-user.target

[Service]
Type=simple
User=$(logname)
ExecStart=/usr/bin/env python3 $SCRIPT_PATH

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable iot_niw.service

echo ""
echo "=========================================================="
echo ""
echo "Installation of data monitoring system is finished"
echo ""
echo "Please reboot the RaspberryPi, just in case :)"
echo ""
echo "=========================================================="
echo ""
exit 0