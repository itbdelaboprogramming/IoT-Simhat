#!/bin/bash
#title           :init_auth.bash
#description     :IoT USB Key feature installation script
#author          :Nicholas Putra Rihandoko
#date            :2023/06/21
#version         :1.2
#usage           :Iot Gateway
#notes           :
#==============================================================================

## Configure IoT USB Key feature
# Enable execute (run program) privilege for all related files
sudo chmod +x /home/$(logname)/NIW/key_code/starter.py
sudo chmod +x /home/$(logname)/NIW/key_code/backup.py
sudo chmod +x /home/$(logname)/NIW/key_code/auth.py
sudo chmod +x /home/$(logname)/NIW/key_code/src/jobs.py
sudo chmod +x /home/$(logname)/NIW/key_code/src/get_usb.bash
sudo chmod +x /etc/crontab

## Create the dependency files
# File paths to create
file_paths=(
"/home/$(logname)/NIW/key_code/src/jobs.txt"
"/home/$(logname)/NIW/key_code/src/status.txt"
"/home/$(logname)/NIW/key_code/src/encryptor.txt"
"/home/$(logname)/NIW/key_code/src/keyword.txt"
"/home/$(logname)/NIW/key_code/iot_key.txt"
)
# Loop through the list of file paths
for file_path in "${file_paths[@]}"; do
# Check if the file already exists
if [ ! -e "$file_path" ]; then
# Create the file
echo "" > "$file_path"
fi
# Set the permissions
chmod 777 "$file_path"
done

## Install necessary packages:
sudo apt update
sudo apt install python3-pip -y
sudo apt install python3-pyudev
sudo apt install python3-psutil
sudo apt install python3-cryptography
sudo apt install python3-pyzipper

# 'zerotier' for virtual LAN and remote access
sudo apt install curl nmap -y
curl -s https://install.zerotier.com | sudo bash
# cron for task automation
sudo apt install cron -y
sudo systemctl enable cron
# ssh and VNC for remote access
if ! systemctl is-enabled --quiet ssh; then
  sudo systemctl enable --now ssh
fi
if ! systemctl is-enabled --quiet vncserver-x11-serviced; then
  sudo raspi-config nonint do_vnc 0
fi

## Run auth.py to configure keyword
sudo python3 /home/$(logname)/NIW/key_code/auth.py generate

## Configure automatic run for every reboot
# Create cron command to check connection every 2 minutes, stars dial.bash if there is no internet
line='*/2 * * * * root python3 /home/$(logname)/NIW/key_code/starter.py & >> /home/$(logname)/NIW/key_code/src/starter.log 2>&1'
# Check whether the command line already exists in /etc/crontab, add or uncomment it if it does not

if [ ! -f "/etc/cron.d/auth" ]; then
  touch "/etc/cron.d/auth"
fi

sudo chmod 644 "/etc/cron.d/auth"
sudo su -c "sed -i '/.*key_code.*/d' /etc/crontab"
sudo su -c "sed -i '/.*key_code.*/d' /etc/cron.d/auth"
sudo su -c "echo \"$line\" >> /etc/cron.d/auth"
# Restart cron service
sudo service cron restart && sudo systemctl restart cron
sleep 1
echo "Installation of IoT USB Key system is completed"
echo ""
python3 /home/$(logname)/NIW/key_code/src/jobs.py kill > /dev/null 2>&1 &
sleep 1
python3 /home/$(logname)/NIW/key_code/starter.py #&
exit
