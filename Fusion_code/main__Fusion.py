"""
#title           :main__Fusion.py
#description     :Handle Modbus, Canbus, and ADDA transfer data
#author          :Nicholas Putra Rihandoko, Nauval Chantika
#date            :2024/02/04
#version         :1.0
#usage           :Energy Monitoring System, RS-485, RS-232C, TWAI, Analog Digital interface
#notes           :
#python_version  :3.9.2
#==============================================================================
"""

# Import library
import datetime # RTC Real Time Clock
import time
import os
import socket
import threading
import logging
from queue import Queue
import query
# modbus libraries
from pymodbus.client import ModbusSerialClient as ModbusClient
from lib.MODbus import kyuden_battery_72kWh as battery
from lib.MODbus import yaskawa_D1000 as converter
from lib.MODbus import yaskawa_GA500 as inverter
from lib.MODbus import tristar_MPPT as charger
#from lib.MODbus import omron_KMN1FLK as kmn1
#from lib.MODbus import omron_KM50C1FLK as km50c1
#from lib.MODbus import msystem_M5XWTU113 as msystem

# canbus libraries
import can # code packet for CANbus communication
#from lib.CANbus import toshiba_SCiB as toshiba

# ADDA libraries
import RPi.GPIO as GPIO
#from lib.ADDA import ADS1256
#from lib.ADDA import DAC8532

# Logging and debugging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
#query.debugging()  # Monitor Modbus communication for debugging

# Socket communication parameters
UNIX_SOCKET_PATH = '/tmp/ipc_socket'   #AF_UNIX
INET_SOCKET_PATH = ('127.0.0.1', 9000) #AF_INET
QUEUE = Queue()

# Data collecting parameters
INTERVAL     = 0   # the period between each subsequent communication routine/loop (in seconds)

# Database uploading parameters
DB_TIMEOUT   = 3 # the maximum time this device will wait for completing MySQl query (in seconds)
DB_INTERVAL  = 5 # the period between each subsequent update to database (in seconds)
FILENAME_REALTIME   = 'data_realtime_log.csv'
FILENAME_RECAP      = 'data_recap_log.csv'

    # Database by SQL
"""
server= {"host":"<URL / IP address>", "user":"<account / root username>", 
         "password":"<account / root password>", "db":"<db name>", "table":"<table name>",
         "port":"3306"}
         
AWS server = "machinedatanglobal.c4sty2dpq6yv.ap-northeast-1.rds.amazonaws.com","Nglobal_root_NIW","Niw_Machinedata_11089694","NEPOWER_X","dataparameter"
local server = "10.4.171.204","root","niw2082023"
"""
SQL_SERVER_REALTIME = {"host":"machinedatanglobal.c4sty2dpq6yv.ap-northeast-1.rds.amazonaws.com",
                       "user":"Nglobal_root_NIW",
                       "password":"Niw_Machinedata_11089694",
                       "db":"NEPOWER_3",
                       "table":"dataparameter",
                       "port":3306}
SQL_SERVER_RECAP    = {"host":"******",
                       "user":"******",
                       "password":"******",
                       "db":"******",
                       "table":"******",
                       "port":3306}

    # Database by FTP
"""
server= {"host":"<URL / IP address>", "user":"<account / root username>", 
         "password":"<account / root password>", "path":"<folders/to/files>}
example = "13.115.57.147","NIW0JET1","123456789","/MicroHydro/NIW0JET1/UNIT1"
"""
FTP_SERVER_REALTIME = {"host":"******",
                       "user":"******",
                       "password":"******",
                       "path":"******"}
FTP_SERVER_RECAP    = {"host":"******",
                       "user":"******",
                       "password":"******",
                       "path":"******"}

# Define Modbus communication parameters
MOD_PORT0            = '/dev/ttyAMA0'    # for RS485/CAN Hat
MOD_PORT_ID1        = 'Prolific_Technology_Inc' # for USB-to-RS232C adaptor
MOD_PORT1           = os.popen('sudo bash {}/get_usb.bash {}'.format(os.path.dirname(os.path.abspath(__file__)), MOD_PORT_ID1)).read().strip()
MOD = {"METHOD":'rtu', "BYTESIZE":8, "STOPBITS":1, "PARITY":'N', "BAUDRATE":9600, "LATENCY":100, "TIMEOUT":1}
#MOD = {"METHOD":'rtu', "BYTESIZE":8, "STOPBITS":1, "PARITY":'E', "BAUDRATE":9600, "LATENCY":100, "TIMEOUT":1}
"""
METHODS : 'rtu'
BYTESIZE: 7 or 8
STOPBITS: 1 or 2
PARITY  : 'N', 'O', or 'E'
BAUDRATE: multiplication of 9600 # data/byte transmission speed (in bytes per second)
LATENCY : # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
TIMEOUT : # the maximum time the master/client will wait for response from slave/server (in seconds)
"""

# Define Canbus communication parameters
CAN = {"BUSTYPE":'socketcan', "CHANNEL":'can0', "BITRATE":250000, "RESTART":100, "TIMEOUT":2}
"""
BUSTYPE : 'socketcan' # CANbus interface for Waveshare RS485/CAN Hat module
CHANNEL : 'can0' # location of channel used for CANbus Communication
BITRATE : 250000 # Toshiba SCiB speed of CANbus = 250000
RESTART : # the time it takes to restart CANbus communication if it fails (in milisecond)
TIMEOUT : # the maximum time the master/client will wait for response from slave/server (in seconds)
"""

# Define ADDA parameters
ADDA = {"VREF_AD":5, "VREF_DA":5, "DMAX_AD":0x7fffff, "DMAX_DA":0xffff}
"""
VREF_AD : #either 3.3 or 5
"""

def setup_modbus():
    global MOD, MOD_PORT0, MOD_PORT1
    # Set each Modbus communication port specification
    client0 = ModbusClient(port=MOD_PORT0, method=MOD["METHOD"], stopbits=MOD["STOPBITS"], bytesize=MOD["BYTESIZE"], parity=MOD["PARITY"], baudrate=MOD["BAUDRATE"], timeout=MOD["TIMEOUT"])
    client1 = ModbusClient(port=MOD_PORT1, method=MOD["METHOD"], stopbits=MOD["STOPBITS"], bytesize=MOD["BYTESIZE"], parity=MOD["PARITY"], baudrate=MOD["BAUDRATE"], timeout=MOD["TIMEOUT"])
    # Connect to the Modbus serial
    client0.connect()
    client1.connect()
    # Define the Modbus slave/server (nodes) objects
    
    # MODBUS NEPOWER
    bat  = battery.node(slave=1, name='BATTERY', client=client1, delay=MOD["STOPBITS"], max_count=20, increment=1, shift=0)
    conv = converter.node(slave=2, name='CONVERTER', client=client0, delay=MOD["STOPBITS"], max_count=20, increment=1, shift=0)
    inv  = inverter.node(slave=3, name='INVERTER', client=client0, delay=MOD["STOPBITS"], max_count=20, increment=1, shift=0)
    crg  = charger.node(slave=4, name='SOLAR CHARGER', client=client0, delay=MOD["STOPBITS"])
    server = [conv, bat, inv, crg]
    
    
    """
    MODBUS OMRON USING FTP
    #ct1 = kmn1.node(slave=3, name='OMRON CT1', client=client0, delay=MOD["LATENCY"], max_count=20, increment=2, shift=0)
    #ct2 = kmn1.node(slave=2, name='OMRON CT2', client=client0, delay=MOD["LATENCY"], max_count=20, increment=2, shift=0)
    #ct3 = msystem.node(slave=1, name='MSYSTEM', client=client0, delay=MOD["LATENCY"], max_count=20, increment=2, shift=2)
    #ct4 = km50.node(slave=4, name='KM50', client=client0, delay=MOD["LATENCY"], max_count=20, increment=1, shift=0)
    #server = [ct1,ct2,ct3]
    """
    #server = []
    
    return server

def read_modbus(server):
    
    # MODBUS NEPOWER
    addr=[["DC_Voltage_Command","AC_Voltage","AC_Current","DC_Power","AC_Frequency","Power_Factor","AC_Power","Consumed_Power_kWh","Produced_Power_kWh"],
          ["SOC","Total_Voltage","Cell_Voltage_avg","Temperature_avg"],
          ["Output_Frequency","Output_Current","Output_Voltage","AC_Power"],
          ["V_PU","I_PU"]]
    
    
    """
    # MODBUS OMRON USING FTP
    addr=[["Active_Power","Generated_Active_Energy_kWh","Voltage_1","Current_1"]#,
          #["Active_Power","Generated_Active_Energy_kWh","Voltage_2","Current_2"]
          ]
    """
    
    #addr=[]
    
    
    for i in range(len(server)):
        try:
            server[i].send_command(command="read",address=addr[i])
        except Exception as e:
            # Print the error message
            print("(modbus) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")
            
def write_modbus(server): #,data):
    #return
    for i in range(len(server)):
        try:
            pass
        except Exception as e:
            # Print the error message
            print("(modbus) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")

def setup_canbus():
    global CAN
    # Configure and bring up the SocketCAN network interface
    #os.system('sudo modprobe can && sudo modprobe can_raw') # load SocketCAN related kernel modules
    #os.system('sudo ip link set down {}'.format(CAN["CHANNEL"])) # disable can0 before config to implement changes in bitrate settings
    #os.system('sudo ip link set {} type can bitrate {} restart-ms {}'.format(CAN["CHANNEL"],CAN["BITRATE"],CAN["RESTART"])) # configure can0 & set to 250000 bit/s
    #os.system('sudo ip link set up {}'.format(CAN["CHANNEL"])) # enable can0 so configuration take effects
    # Set each CANbus communication port specification
    #client = can.interface.Bus(bustype=CAN["BUSTYPE"], channel=CAN["CHANNEL"], bitrate=CAN["BITRATE"])
    # Define the Modbus slave/server (nodes) objects
    # CANBUS TOSHIBA
    #bat = toshiba.node(name='TOSHIBA BATTERY', client=client, timeout=CAN["TIMEOUT"])
    #server = [bat]
    server = []
    return server

def read_canbus(server):
    """
    # addr can be written by several format
    #addr = [0x050, 0x053, 0x055, 0x056]
    #addr = [[0x050,1], [0x055,3], [0x056,1], [0x056,3]]
    #addr = ["Module_Current_1","Module_Current_2","Module_Voltage_1","Module_Voltage_2","Temperature_1","Temperature_2"]
    """
    #addr = ["Module_Current_1","Module_Current_2","Module_Voltage_1","Module_Voltage_2","Temperature_1","Temperature_2"]
    addr=[]
    for i in range(len(server)):
        try:
            server[i].send_command(command="receive",address=addr)
        except Exception as e:
            # Print the error message
            print("(canbus) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")
            
def write_canbus(server): #,data):
    #return
    for i in range(len(server)):
        try:
            pass
        except Exception as e:
            # Print the error message
            print("(canbus) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")

def setup_ADDA():
    global ADDA
    #ADC = ADS1256.ADS1256(name='ADC1',bus=0,device=1,rst=18,drdy=17,cs_adc=22) # rst, drdy, and cs_adc are pin number input
    #DAC = DAC8532.DAC8532(name='DAC1',bus=0,device=1,cs_dac=23,A=0x30,B=0x34,DAC_MAX=ADDA["DMAX_DA"],DAC_VREF=ADDA["VREF_DA"]) # cs_dac is pin number input
    #server_AD = [ADC]
    #server_DA = [DAC]
    server_AD = []
    server_DA = []
    return server_AD, server_DA

def read_ADDA(server):
    global ADDA
    #limit = [[[0x000000,ADDA["DMAX_AD"],0,ADDA["VREF_AD"]],[0x000000,ADDA["DMAX_AD"],0,ADDA["VREF_AD"]],[0x000000,ADDA["DMAX_AD"],0,ADDA["VREF_AD"]],[0x000000,ADDA["DMAX_AD"],0,ADDA["VREF_AD"]],
    #          [0x000000,ADDA["DMAX_AD"],0,ADDA["VREF_AD"]],[0x000000,ADDA["DMAX_AD"],0,ADDA["VREF_AD"]],[0x000000,ADDA["DMAX_AD"],0,ADDA["VREF_AD"]],[0x000000,ADDA["DMAX_AD"],0,ADDA["VREF_AD"]]]
    #        ]
    
    # Limit for current output signal
    # 1. Check resistor value for the converting current to voltage
    # 2. current sensor oftenly have range (4-20mA), find the min and max voltage value of output
    # 3. after find the min and max voltage value, find the min and max digital value of output
    # 4. do remapping from digital value range to actual unit from data sensor
    #example: pressure sensor 0-1 MPa has 4-20mA output & use 220 ohm resistor
    # voltage output range: (0.88-4.4 V) & voltage input ADC: (0-5 V)
    # digital output range: (0x16872B-0x70A3D6) & digital input ADC: (0x000000-0x7FFFFF)
    # the limit will be [0x16872B,0x70A3D6,0,1]
    
    # [0~1 MPa, 0~40 L/min, reserved, reserved, reserved, -4710~4710 W, 0~750 rpm, -60~60 Nm]
    """
    limit = [[[0x16872B,0x70A3D6,0,1],[0x16872B,0x70A3D6,0,40],[0x000000,0x7FFFFF,0,ADDA["VREF_AD"]],
              [0x000000,0x7FFFFF,0,ADDA["VREF_AD"]],[0x000000,0x7FFFFF,0,ADDA["VREF_AD"]],[0x000000,0x7FFFFF,-4658.0,4762.0],
              [0x000000,0x7FFFFF,-4.725,745.275],[0x000000,0x7FFFFF,-59.335,60.665]]
            ]
    rounded = [[3,2,2,2,2,0,0,2]]
    """
    limit = [[[]]]
    rounded = [[]]
    
    for i in range(len(server)):
        try:
            for j in range(0,8,1):
                float_val = remap(server[i].ADS1256_GetChannalValue(j),limit[i][j][0],limit[i][j][1],limit[i][j][2],limit[i][j][3])
                server[i].Value[j] = round_digits(float_val,rounded[i][j])
        except Exception as e:
            # Print the error message
            print("(ADDA) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")
            
def write_ADDA(server): #,data):
    # return
    global ADDA
    #limit = [[[0,ADDA["VREF_DA"],0x0000,ADDA["DMAX_DA"]],[0,ADDA["VREF_DA"],0x0000,ADDA["DMAX_DA"]]]
    #        ]
    limit = [[[]]]
    for i in range(len(server)):
        try:
            val_A = int(remap(server[i].Value[0],limit[i][0][0],limit[i][0][1],limit[i][0][2],limit[i][0][3]))
            val_B = int(remap(server[i].Value[1],limit[i][1][0],limit[i][1][1],limit[i][0][2],limit[i][0][3]))
            server[i].DAC8532_Write_Data(server[i]._channel_A, val_A)
            server[i].DAC8532_Write_Data(server[i]._channel_B, val_B)
        except Exception as e:
            # Print the error message
            print("(ADDA) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")

def remap(value, old_min, old_max, new_min, new_max):
    # Map the value from the old range to the new range
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

def round_digits(value, ndigits):
    """
    Round a value to a specified number of decimal places and return as a string
    with the specified number of decimals. Ensures that if the value is effectively
    zero after rounding, it is set to positive 0.0, maintaining the decimal places.

    :param value: Float value to round.
    :param ndigits: Number of decimal places to round to.
    :return: String representing the rounded value with specified decimal places.
    """
    # Round the value and adjust for zero
    adjusted_value = round(value, ndigits)
    if adjusted_value == 0:
        adjusted_value = 0.0
    # Format the number as a string with the specified number of decimal places
    #adjusted_value = f"{adjusted_value:.{ndigits}f}"
    return adjusted_value

def data_processing(server, timer):
    cpu_temp = query.get_cpu_temperature()
    
    # MODBUS NEPOWER
    title = ["time","cpu_Temp","bat_Temp",
             "bat_soc","bat_ttl_V","bat_avg_V",
             "con_out_V_ref","con_in_V","con_in_A",
             "con_out_kW","con_in_Hz","con_in_PF",
             "con_in_kW","con_consume_kWh","con_produce_kWh",
             "inv_out_Hz","inv_out_A","inv_out_V_ref","inv_out_kWh"] #,"crg_out_V", "crg_out_A"]
             
    data = [timer.strftime("%Y-%m-%d %H:%M:%S"), cpu_temp, server[1].Temperature_avg,
            server[1].SOC, server[1].Total_Voltage, server[1].Cell_Voltage_avg,
            server[0].DC_Voltage_Command, server[0].AC_Voltage, server[0].AC_Current,
            server[0].DC_Power, server[0].AC_Frequency, server[0].Power_Factor,
            server[0].AC_Power, server[0].Consumed_Power_kWh, server[0].Produced_Power_kWh,
            server[2].Output_Frequency, server[2].Output_Current, server[2].Output_Voltage, server[2].AC_Power] #,server[3].V_PU, server[3].I_PU]
    
    
    """
    
    data = [timer.strftime("%Y-%m-%d"),timer.strftime("%H:%M:%S"),
            (server[0].Active_Power*100),(server[0].Generated_Active_Energy_kWh*10),
            0,(server[0].Voltage_1*10),(server[0].Current_1*10),(0*1000),
            (0*100),(0*1000),(0*1),(0*100),(0*1),(0*10),(0*10),0,0,0,0,0,
            0,0,0,0,0,(0*10),(0*1),(0*10)
           ]
    """
    
    """
    # CANBUS TOSHIBA
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
    """
    
    # MicroHydro
    """
    title = ["DATE","TIME","バッテリ出力(W)","発電量(Wh)","水車.発電機回転数(rpm)",
             "発電機電圧(Ｖdc)","発電機電流(A)","reserved", "reserved","水圧(Mpa)","流量(L/min)",
             "抵抗機電流(A)","reserved","バッテリ電圧(Ｖ)","バッテリ電流(A)","reserved",
             "reserved","reserved","reserved","reserved","reserved","reserved",
             "reserved","reserved","reserved","発電機出力(W)",
             "reserved","水車トルク(N-m)","水車出力(W)"
             ]
    """
    """
    title = ["date_entry","time_entry","currently_generating_power","cumulative_power_generation","generator_speed",
             "generator_voltage","generator_current","today_three_phase_power_generation", "guide_vane_opening","water_pressure","flow_rate",
             "efficiency","water_level","grid_voltage","grid_current","grid_interconnection_bool",
             "mcb1_breaker_trip_bool","discharge_resistance_overheating_bool","breaking_unit_abnormal_bool","generator_overheating_bool","inverter_abnormal_bool","generator_functioning_bool",
             "generator_operation_preperation_bool","grid_interconnection_converter_bool","system_interconnection_operation_preperation_bool","generator_power_kw",
             "generator_after_vdc","recorded_time_from_ftp_to_db","axel_temp1","axel_temp2"
             ]
    
    data = [timer.strftime("%Y-%m-%d"), timer.strftime("%H:%M:%S"), 0, 0,
            server[0].Value[6], 0, 0, 0, 0, server[0].Value[0], server[0].Value[1],
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, timer.strftime("%Y-%m-%d H:%M:%S"),
            server[0].Value[7], server[0].Value[5]*10, 
            ]
    """
    return title, data

########################################################################
def socket_client_thread(data_queue):
    while True:
        try:
            # Connect to the server
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(UNIX_SOCKET_PATH)
                while True:
                    # Wait for new data to be placed in the queue
                    data_to_send = data_queue.get()
                    # Send data
                    sock.sendall(','.join(map(str, data_to_send)).encode('utf-8'))
                    # Sleep for the interval
                    time.sleep(INTERVAL)
        except Exception as e:
            logging.error("Socket communication error: %s", e)
            # Sleep briefly before retrying
            time.sleep(1)
########################################################################
def main():
    init = True  # variable to check initialization
    # Checking the connection
    while init:
        try:
            # Setup Raspberry Pi as client/master
            server_modbus = setup_modbus()
            logging.info("Connected to MODbus Communication")
            #print("<===== Connected to MODbus Communication =====>")
            #print("")
            server_canbus = setup_canbus()
            logging.info("Connected to CANbus Communication")
            #print("<===== Connected to CANbus Communication =====>")
            #print("")
            server_AD, server_DA = setup_ADDA()
            #server_DA[0].Value = [0,0]
            logging.info("Connected to ADDA Module")
            #print("<========= Connected to  ADDA Module =========>")
            #print("")
            init = False
        except Exception as e:
            # Print the error message
            logging.error("Problem with Setup process: %s", e)
            #print("<===== ===== retrying ===== =====>")
            #print("")
            time.sleep(3)
    
    # Start the socket communication thread
    #client_thread = threading.Thread(target=socket_client_thread, args=(QUEUE,), daemon=True)
    #client_thread.start()
    
    first = [True, True]
    # Reading messages and Upload to database sequence
    while not init:
        try:
            # First run (start-up) sequence
            if first[0]:
                first[0] = False
                # time counter
                start = datetime.datetime.now()
                real_time = start
                recap_time = start
                write_modbus(server_modbus)
                #write_canbus(server_canbus)
                write_ADDA(server_DA)
            
            # Send the command to read the measured value and do all other things
            read_modbus(server_modbus)
            read_canbus(server_canbus)
            read_ADDA(server_AD)
            timer = datetime.datetime.now()
            server = server_modbus + server_canbus + server_AD + server_DA
            query.print_response(server, timer)
            title, data = data_processing(server, timer)
            QUEUE.put(data)  # Put the processed data into the queue

            # Check elapsed time
            if (timer - start).total_seconds() > DB_INTERVAL or first[1] == True:
                start = timer
                first[1] = False
                # Update/push data to database
                query.update_SQL(title, data, timer, FILENAME_REALTIME, SQL_SERVER_REALTIME, real_time, 0, DB_TIMEOUT)
                #query.update_SQL(title, data, timer, FILENAME_RECAP, SQL_SERVER_RECAP, recap_time, 43200, DB_TIMEOUT*144)
                #query.update_FTP(title, data, timer, FILENAME_REALTIME, FTP_SERVER_REALTIME, real_time, 0, DB_TIMEOUT)
                #query.update_FTP(title, data, timer, FILENAME_RECAP, FTP_SERVER_RECAP, recap_time, 43200, DB_TIMEOUT*144)
                
            time.sleep(INTERVAL)
    
        except Exception as e:
            # Print the error message
            logging.error("Encountered an error: %s", e)
            #print(e)
            #print("<===== ===== retrying ===== =====>")
            #print("")
            time.sleep(3)
            
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Shutting down client.")
        # Ensure resources are closed properly.
