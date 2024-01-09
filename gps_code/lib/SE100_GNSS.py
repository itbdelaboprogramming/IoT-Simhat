"""
#title           :SE100_GNSS.py
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
        self._ser = serial.Serial(port,9600,timeout=3)
        self._ser.flushInput()
        print('Start GPS session...')

    def gps_decode(self,gps_data):
        # Calculate Latitude and Longitude
        Lat = round(float(gps_data[1][:gps_data[1].index('.')-2])+(float(gps_data[1][gps_data[1].index('.')-2:])/60),7)
        Long = round(float(gps_data[3][:gps_data[3].index('.')-2])+(float(gps_data[3][gps_data[3].index('.')-2:])/60),7)
        if gps_data[2] == 'N': self.Latitude = Lat
        else: self.Latitude = -Lat
        if gps_data[4] == 'E': self.Longitude = Long
        else: self.Longitude = -Long

        # Decode the other data
        self.RTC = datetime.datetime.strptime(gps_data[0][:-3],'%H%M%S').time()
        self.Count_Satellites = int(gps_data[6])
        self.HDOP = float(gps_data[7])
        if self.HDOP > 1: self.Status = "Poor GPS Accuracy"
        else: self.Status = "Good GPS Accuracy"

    def handle_timeout(self, signum, frame):
        raise TimeoutError("-- no data on serial port --")

    def read_gps(self):
        try:
            signal.alarm(2)  # Start the timeout countdown
            while True:
                # Decode the data from GPS SE100 NMEA serial communication
                line = self._ser.readline().decode('utf-8', errors='replace')
                # Select the $GNGGA only
                if '$GNGGA,' in line:
                    if ',,,,' in line:
                        # EXAMPLE LOST SIGNAL: '$GNGGA,,,,,,0,00,99.99,,,,,,*56'
                        self.Status = "GPS Signal Lost"
                        break
                    elif datetime.datetime.utcnow().strftime("%H%M%S") in line:
                        # Parse the from NMEA format to object's attributes
                        data = str(line).replace('$GNGGA,',"").strip().split(',')
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