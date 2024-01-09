"""
#title           :main__modbus.py
#description     :modbus Communication between Modbus devices and Raspberry Pi + RS485/CAN Hat + USB-to-RS232C Adaptor
#author          :Nicholas Putra Rihandoko, Nauval Chantika
#date            :2023/09/22
#version         :1.0
#usage           :Energy Monitoring System, RS-485 and RS-232C interface
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
from pymodbus.client import ModbusSerialClient as ModbusClient
from queue import Queue
import query
from lib import kyuden_battery_72kWh as battery
from lib import yaskawa_D1000 as converter
from lib import yaskawa_GA500 as inverter
#from lib import tristar_MPPT as charger

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define Modbus communication parameters
PORT0            = '/dev/ttyAMA0'    # for RS485/CAN Hat
PORT_ID1        = 'Prolific_Technology_Inc' # for USB-to-RS232C adaptor
PORT1           = os.popen('sudo bash {}/get_usb.bash {}'.format(os.path.dirname(os.path.abspath(__file__)), PORT_ID1)).read().strip()
METHOD          = 'rtu'
BYTESIZE        = 8
STOPBITS        = 1
PARITY          = 'N'
BAUDRATE        = 9600   # data/byte transmission speed (in bytes per second)
CLIENT_LATENCY  = 100   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
TIMEOUT         = 1   # the maximum time the master/client will wait for response from slave/server (in seconds)
INTERVAL        = 3   # the period between each subsequent communication routine/loop (in seconds)

# Define MySQL Database parameters
SQL_SERVER    = {"host":"machinedatanglobal.c4sty2dpq6yv.ap-northeast-1.rds.amazonaws.com",
                    "user":"Nglobal_root_NIW",
                    "password":"Niw_Machinedata_11089694",
                    "db":"NEPOWER_1",
                    "table":"dataparameter",
                    "port":3306}
#SQL_SERVER    = {"host":"10.4.171.204",
#                    "user":"root",
#                    "password":"niw2082023",
#                    "db":"test",
#                    "table":"not_used",
#                    "port":3306}
SQL_TIMEOUT   = 3 # the maximum time this device will wait for completing MySQl query (in seconds)
SQL_INTERVAL  = 60 # the period between each subsequent update to database (in seconds)
FILENAME = 'modbus_log.csv'

# Socket communication parameters
UNIX_SOCKET_PATH = '/tmp/ipc_socket'   #AF_UNIX
INET_SOCKET_PATH = ('127.0.0.1', 9000) #AF_INET

#query.debugging()  # Monitor Modbus communication for debugging
QUEUE = Queue()

def setup_modbus():
    global PORT0, PORT1, METHOD, BYTESIZE, STOPBITS, PARITY, BAUDRATE, CLIENT_LATENCY, TIMEOUT
    # Set each Modbus communication port specification
    client0 = ModbusClient(port=PORT0, method=METHOD, stopbits=STOPBITS, bytesize=BYTESIZE, parity=PARITY, baudrate=BAUDRATE, timeout=TIMEOUT)
    client1 = ModbusClient(port=PORT1, method=METHOD, stopbits=STOPBITS, bytesize=BYTESIZE, parity=PARITY, baudrate=BAUDRATE, timeout=TIMEOUT)
    # Connect to the Modbus serial
    client0.connect()
    client1.connect()
    # Define the Modbus slave/server (nodes) objects
    bat  = battery.node(slave=1, name='BATTERY', client=client1, delay=CLIENT_LATENCY, max_count=20, increment=1, shift=0)
    conv = converter.node(slave=2, name='CONVERTER', client=client0, delay=CLIENT_LATENCY, max_count=20, increment=1, shift=0)
    inv  = inverter.node(slave=3, name='INVERTER', client=client0, delay=CLIENT_LATENCY, max_count=20, increment=1, shift=0)
    #chr = charger.node(slave=4, name='SOLAR CHARGER', client=client, delay=CLIENT_LATENCY)
    server = [conv, bat, inv]
    return server

def read_modbus(server):
    addr=[["DC_Voltage_Command","AC_Voltage","AC_Current","DC_Power","AC_Frequency","Power_Factor","AC_Power","Consumed_Power_kWh","Produced_Power_kWh"],
          ["SOC","Total_Voltage","Cell_Voltage_avg","Temperature_avg"],
          ["Output_Frequency","Output_Current","Output_Voltage","AC_Power"]]
    
    for i in range(len(server)):
        try:
            server[i].send_command(command="read",address=addr[i])
        except Exception as e:
            # Print the error message
            print("(modbus) problem with",server[i]._name,":")
            print(e)
            print("<===== ===== continuing ===== =====>")
            print("")
            
def write_modbus(server):
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
        
def data_processing(server, timer):
    cpu_temp = query.get_cpu_temperature()
    
    title = ["time","cpu_Temp","bat_Temp",
             "bat_soc","bat_ttl_V","bat_avg_V",
             "con_out_V_ref","con_in_V","con_in_A",
             "con_out_kW","con_in_Hz","con_in_PF",
             "con_in_kW","con_consume_kWh","con_produce_kWh",
             "inv_out_Hz","inv_out_A","inv_out_V_ref","inv_out_kWh"]
    
    data = [timer.strftime("%Y-%m-%d %H:%M:%S"), cpu_temp, server[1].Temperature_avg,
            server[1].SOC, server[1].Total_Voltage, server[1].Cell_Voltage_avg,
            server[0].DC_Voltage_Command, server[0].AC_Voltage, server[0].AC_Current,
            server[0].DC_Power, server[0].AC_Frequency, server[0].Power_Factor,
            server[0].AC_Power, server[0].Consumed_Power_kWh, server[0].Produced_Power_kWh,
            server[2].Output_Frequency, server[2].Output_Current, server[2].Output_Voltage, server[2].AC_Power]
    
    return title, data

def update_database(title, data, timer):
    global SQL_SERVER,FILENAME
    # Define MySQL queries and data which will be used in the program
    cpu_temp = query.get_cpu_temperature()
    sql_query = ("INSERT INTO `{}` ({}) VALUES ({})".format(SQL_SERVER["table"],
                                                                ",".join(title),
                                                                ",".join(['%s' for _ in range(len(title))])))

    query.log_in_csv(title ,data, timer, FILENAME)
    query.retry_mysql(SQL_SERVER, sql_query, FILENAME, SQL_TIMEOUT)
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
    init = True  # variable to check Modbus initialization
    # Checking the connection Modbus
    while init:
        try:
            # Setup Raspberry Pi as Modbus client/master
            server = setup_modbus()
            logging.info("Connected to Modbus Communication")
            #print("<===== Connected to Modbus Communication =====>")
            #print("")
            init = False
        except Exception as e:
            # Print the error message
            logging.error("(modbus) Problem with Modbus communication: %s", e)
            #print("<===== ===== retrying ===== =====>")
            #print("")
            time.sleep(3)
    
    # Start the socket communication thread
    client_thread = threading.Thread(target=socket_client_thread, args=(QUEUE,), daemon=True)
    client_thread.start()
    
    first = [True, True]
    # Reading a Modbus message and Upload to database sequence
    while not init:
        try:
            # First run (start-up) sequence
            if first[0]:
                first[0] = False
                # time counter
                start = datetime.datetime.now()
                write_modbus(server)
            
            # Send the command to read the measured value and do all other things
            read_modbus(server)
            timer = datetime.datetime.now()
            query.print_response(server, timer)
            title, data = data_processing(server, timer)
            QUEUE.put(data)  # Put the processed data into the queue

            # Check elapsed time
            if (timer - start).total_seconds() > SQL_INTERVAL or first[1] == True:
                start = timer
                first[1] = False
                # Update/push data to database
                update_database(title, data, timer)
        
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
