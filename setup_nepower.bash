#!/bin/bash
#title           :setup.bash
#description     :setup all NIW code (modbus and canbus)
#author          :Nauval Chantika
#date            :2023/10/25
#version         :0.1
#usage           :setup integration
#notes           :
#==============================================================================

sudo raspi-config nonint do_wayland W1
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_vnc 0
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_rgpio 0

sudo apt update -y
sudo apt upgrade -y
sudo apt install onboard -y

sudo bash NIW/simhat_code/init_dial.bash
sudo bash NIW/modbus_code/init_modbus.bash
sudo bash NIW/canbus_code/init_canbus.bash
#sudo bash NIW/gps_code/init_gps.bash
#sudo bash NIW/key_code/init_auth.bash
#python3 NIW/key_code/src/jobs.py kill
sudo reboot

exit