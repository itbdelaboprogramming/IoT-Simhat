#!/bin/bash
#title           :get_usb.bash
#description     :Script to find the USB key's directory
#author          :Nicholas Putra Rihandoko
#date            :2023/06/12
#version         :1.1
#usage           :IoT Gateway
#notes           :
#==============================================================================

directory="/media/$(logname)"
result=0

# Check if the directory is not empty
if [ "$(ls -A $directory)" ]; then
# Iterate over subdirectories
for subdirectory in "$directory"/*; do
# Check if iot_key.txt file exists in the subdirectory
if [ -f "$subdirectory/iot_key.txt" ]; then
result=1
fi
done
if [ result == 0 ]; then
echo "$directory/devicenotfound"
else
echo "$subdirectory"
fi
fi
exit