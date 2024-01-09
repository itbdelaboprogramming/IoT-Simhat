"""
#title           :SIM7600_GNSS.py
#description     :Main script to obtain GPS data
#author          :Nicholas Putra Rihandoko
#date            :2023/06/21
#version         :0.2
#usage           :Iot Gateway
#notes           :take a look at README.txt for further info
#python_version  :3.7.3
#==============================================================================
"""

#!/usr/bin/python
# -*- coding:utf-8 -*-

import serial
import os
import datetime
import signal

class node:
    def __init__(self,port,name):
        # Intialize variables
        self._name = name
        self.Latitude = None
        self.Longitude = None
        self.RTC = datetime.datetime.now()
        self.Count_Satellites = 0
        self.HDOP = None
        self.Status = "GPS Not Ready"
        signal.signal(signal.SIGALRM, self.handle_timeout)

        # Configure serial communication
        os.system('sudo chmod a+rw {}'.format(port))
        self._ser = serial.Serial(port,115200,timeout=3)
        self._ser.flushInput()
        print('Start GPS session...')

    def gps_decode(self,gps_data):
        # Calculate Latitude and Longitude
        Lat = round(float(gps_data[4][:gps_data[4].index('.')-2])+(float(gps_data[4][gps_data[4].index('.')-2:])/60),7)
        Long = round(float(gps_data[6][:gps_data[6].index('.')-2])+(float(gps_data[6][gps_data[6].index('.')-2:])/60),7)
        if gps_data[5] == 'N': self.Latitude = Lat
        else: self.Latitude = -Lat
        if gps_data[7] == 'E': self.Longitude = Long
        else: self.Longitude = -Long

        # Decode the other data
        Date = datetime.datetime.strptime(gps_data[8],'%d%m%y').date()
        Time = datetime.datetime.strptime(gps_data[9][:-2],'%H%M%S').time()
        self.RTC = datetime.datetime.combine(Date,Time)
        self.Count_Satellites = int(gps_data[1])
        self.HDOP = float(gps_data[13])
        if self.HDOP > 1: self.Status = "Poor GPS Accuracy"
        else: self.Status = "Good GPS Accuracy"

    def handle_timeout(self, signum, frame):
        raise TimeoutError("-- no data on serial port --")

    def read_gps(self):
        try:
            signal.alarm(2)  # Start the timeout countdown
            # Send AT Commands to SIM Hat module using serial communication
            self._ser.write(('AT+CGNSSINFO'+'\r\n').encode())
            # Read AT Command's responses
            while True:
                line = self._ser.readline().decode()
                if '+CGNSSINFO: ' in line:
                    if ',,,,' in line:
                        # EXAMPLE LOST SIGNAL: '+CGNSSINFO: ,,,,,,,,,,,,,,,'
                        self.Status = "GPS Signal Lost"
                        break
                    else:
                        # Parse the from NMEA format to object's attributes
                        data = line.replace('+CGNSSINFO: ',"").strip().split(',')
                        self.gps_decode(data)
                        break
            signal.alarm(0)
            print(self.Status)
        except Exception as e:
            # Print the error message
            print("problem with GPS :")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")
            # Disconnected
            self.Status = "GPS Not Ready"
            self.Count_Satellites = 0
            self.HDOP = None