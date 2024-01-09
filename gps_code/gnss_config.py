"""
#title           :gnss_config.py
#description     :AT command for GNSS configuration script
#author          :Nicholas Putra Rihandoko
#date            :2023/06/21
#version         :1.2
#usage           :Iot Gateway
#notes           :
#python_version  :3.7.3
#==============================================================================
"""
#!/usr/bin/python
# -*- coding:utf-8 -*-

# Import library
import sys
import os
import time
import serial


# send AT command through serial communication, then read and print the response (expect)
def send_at(command,expect,wait):
    rec_buff = ''.encode()
    sim.write((command + '\r\n').encode())
    time.sleep(wait)
    if sim.inWaiting():
        rec_buff = sim.read(sim.inWaiting())
    if expect not in rec_buff.decode():
        print('command ' + command + ' failed')
        print('unexpected response:\t' + rec_buff.decode())
    else:
        print(rec_buff.decode())

if sys.argv[1] == "SIM7600":
    # Connect through serial communication to the SIM Card
    port_id = 'SimTech__Incorporated_SimTech__Incorporated_0123456789ABCDEF-if02' # for SIM7600G-H module
    port = os.popen('sudo bash {}/get_usb.bash {}'.format(os.path.dirname(os.path.abspath(__file__)), port_id)).read().strip()
    sim = serial.Serial(port, baudrate=115200, timeout=3)

    # Access GPS session
    send_at('AT+CGPS=0','OK',5)
    
    # Start GPS session
    send_at('AT+CGPS=1','OK',1)

    # Start GPS automatically
    send_at('AT+CGPSAUTO=1','OK',1)

    # Enable GPS XTRA function
    send_at('AT+CGPSXE=1','OK',1)
    
    # Download XTRA assistant file automatically
    send_at('AT+CGPSXDAUTO=1','OK',1)

    sim.close()
    
else:
    pass
