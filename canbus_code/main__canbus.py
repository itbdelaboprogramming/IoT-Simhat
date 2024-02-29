"""
#title           :main__canbus.py
#description     :CANbus Communication between SCiB Battery and Raspberry Pi
#author          :Fajar Muhammad Noor Rozaqi, Nicholas Putra Rihandoko
#date            :2023/04/03
#version         :2.1
#usage           :BMS-python
#notes           :
#python_version  :3.7.3
#==============================================================================
"""

# Import library
import datetime # RTC Real Time Clock
import time
import os
#import socket
#import threading
#import logging
from queue import Queue
import query
import can # code packet for CANbus communication
from lib import toshiba_SCiB as battery

# Define CANbus communication parameters
BUSTYPE         = 'socketcan' # CANbus interface for Waveshare RS485/CAN Hat module
CHANNEL         = 'can0' # location of channel used for CANbus Communication
BITRATE         = 250000 # Toshiba SCiB speed of CANbus = 250000
RESTART         = 100 # the time it takes to restart CANbus communication if it fails (in milisecond)
TIMEOUT         = 2 # the maximum time the master/client will wait for response from slave/server (in seconds)
INTERVAL       = 30 # the period between each subsequent communication routine/loop (in seconds)

# Define FTP database parameters
FTP_SERVER = {"host":"*HOST*",
                       "user":"*USERNAME*",
                       "password":"*PASSWORD*",
                       "path":"*/folders/inside/server*"}
# Define MySQL Database parameters
SQL_SERVER    = {"host":"******",
                    "user":"******",
                    "password":"******",
                    "db":"******",
                    "table":"******",
                    "port":3306}
SQL_TIMEOUT   = 3 # the maximum time this device will wait for completing MySQl query (in seconds)
SQL_INTERVAL  = 60 # the period between each subsequent update to database (in seconds)
FILENAME = 'canbus_log.csv'

#query.debugging()  # Monitor Modbus communication for debugging

def setup_canbus():
    global BUSTYPE, CHANNEL, BITRATE, RESTART, TIMEOUT
    # Configure and bring up the SocketCAN network interface
    os.system('sudo modprobe can && sudo modprobe can_raw') # load SocketCAN related kernel modules
    os.system('sudo ip link set down {}'.format(CHANNEL)) # disable can0 before config to implement changes in bitrate settings
    os.system('sudo ip link set {} type can bitrate {} restart-ms {}'.format(CHANNEL,BITRATE,RESTART)) # configure can0 & set to 250000 bit/s
    os.system('sudo ip link set up {}'.format(CHANNEL)) # enable can0 so configuration take effects
    client = can.interface.Bus(bustype=BUSTYPE, channel=CHANNEL, bitrate=BITRATE)
    bat = battery.node(name='TOSHIBA BATTERY', client=client, timeout=TIMEOUT)
    server = [bat]
    return server

def read_canbus(server):
    #return
    for i in range(len(server)):
        try:
            server[i].send_command(command="receive",address=[0x050, 0x053, 0x055, 0x056])
            server[i].send_command(command="receive",address=[[0x050,1], [0x055,3], [0x056,1], [0x056,3]])
            server[i].send_command(command="receive",address=["Module_Current_1","Module_Current_2","Module_Voltage_1","Module_Voltage_2","Temperature_1","Temperature_2"])
        except Exception as e:
            # Print the error message
            print("(canbus) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")
            
def write_canbus(server): #,data):
    for i in range(len(server)):
        try:
            pass
        except Exception as e:
            # Print the error message
            print("(canbus) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")

def data_processing(server, timer):
    cpu_temp = query.get_cpu_temperature()
    [bootup_time, uptime, total_uptime, downtime, total_downtime] = query.get_updown_time(mysql_server, timer, mysql_timeout)
    title = ["startup_date","startup_time","uptime","total_uptime",
             "shutdown_date","shutdown_time","downtime","total_downtime",
             "battery_percentage","battery_voltage",
             "rpi_temp","volt_1","volt_2",
             "current_1","current_2","current_total",
             "temp_1","temp_2","temp_avg"]
    
    data = [bootup_time.strftime("%Y-%m-%d"), bootup_time.strftime("%H:%M:%S"), uptime, total_uptime,
            timer.strftime("%Y-%m-%d"), timer.strftime("%H:%M:%S"), downtime, total_downtime,
            server[0].SOC, round((server[0].Module_Voltage_1 + server[0].Module_Voltage_2)/2,2),
            cpu_temp, server[0].Module_Voltage_1, server[0].Module_Voltage_2,
            server[0].Module_Current_1, server[0].Module_Current_2, (server[0].Module_Current_1 + server[0].Module_Current_2),
            server[0].Temperature_1, server[0].Temperature_2, round((server[0].Temperature_1 + server[0].Temperature_2)/2,1)]
    
    return title, data

def update_SQL(title, data, timer, csv_file, sql_server, last_time, interval_upload=0, timeout=3):
    # Define MySQL queries and data which will be used in the program
    sql_query = ("INSERT INTO `{}` ({}) VALUES ({})".format(sql_server["table"],
                                                                ",".join(title),
                                                                ",".join(['%s' for _ in range(len(title))])))

    query.log_in_csv(title ,data, timer, csv_file)
    if (timer - last_time).total_seconds() > interval_upload:
        last_time = timer
        query.retry_mysql(sql_server, sql_query, csv_file, timeout)
#################################################################################################################
init = True  # variable to check CANbus initialization
# Checking the connection CANbus
while init:
    try:
        # Setup Raspberry Pi as Modbus client/master
        server = setup_canbus()
        print("<===== Connected to CANbus Communication =====>")
        print("")
        init = False

    except Exception as e:
        # Print the error message
        print("problem with CANbus communication:")
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)

first = [True, True]
# Reading a CANbus message and Upload to database sequence
while not init:
    try:
        # First run (start-up) sequence
        if first[0]:
            first[0] = False
            # time counter
            start = datetime.datetime.now()
            last_update_time = start
            
        # Send the command to read the measured value and do all other things
        read_canbus(server)
        timer = datetime.datetime.now()
        query.print_response(server, timer)
        title, data = data_processing(server, timer)

        # Check elapsed time
        if (timer - start).total_seconds() > SQL_INTERVAL or first[1] == True:
            start = timer
            first[1] = False
            # Update/push data to database
            update_SQL(title, data, timer, FILENAME, SQL_SERVER, last_update_time, 0, SQL_TIMEOUT)
            #query.update_FTP(title, data, timer, FILENAME, FTP_SERVER, last_update_time, 0, SQL_TIMEOUT)
        
        time.sleep(INTERVAL)
    
    except Exception as e:
        # Print the error message
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)
