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
from queue import Queue
import query
from pymodbus.client import ModbusSerialClient as ModbusClient
from lib import omron_KMN1FLK as kmn1
#from lib import omron_KM50C1FLK as km50c1
#from lib import msystem_M5XWTU113 as msystem
#from lib import electricPowerCalc as calc

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define Modbus communication parameters
PORT0            = '/dev/ttyAMA0'    # for RS485/CAN Hat
#PORT_ID1        = 'Prolific_Technology_Inc' # for USB-to-RS232C adaptor
#PORT1           = os.popen('sudo bash {}/get_usb.bash {}'.format(os.path.dirname(os.path.abspath(__file__)), PORT_ID1)).read().strip()
METHOD          = 'rtu'
BYTESIZE        = 8
STOPBITS        = 1
PARITY          = 'E'
BAUDRATE        = 9600   # data/byte transmission speed (in bytes per second)
CLIENT_LATENCY  = 100   # the delay time master/client takes from receiving response to sending a new command/request (in milliseconds)
TIMEOUT         = 1   # the maximum time the master/client will wait for response from slave/server (in seconds)
INTERVAL        = 10   # the period between each subsequent communication routine/loop (in seconds)


# Define FTP database parameters
FTP_SERVER_REALTIME = {"host":"13.115.57.147",
                       "user":"NIW0JET1",
                       "password":"123456789",
                       "path":"/MicroHydro/NIW0JET1/UNIT1"}
FTP_SERVER_RECAP    = {"host":"13.115.57.147",
                       "user":"NIW0JET1",
                       "password":"123456789",
                       "path":"/MicroHydro/NIW0JET1/UNIT2"}

# Define MySQL Database parameters
#SQL_SERVER_REALTIME = {"host":"machinedatanglobal.c4sty2dpq6yv.ap-northeast-1.rds.amazonaws.com",
#                       "user":"Nglobal_root_NIW",
#                       "password":"Niw_Machinedata_11089694",
#                       "db":"NEPOWER_1",
#                       "table":"dataparameter1",
#                       "port":3306}
#SQL_SERVER_RECAP    = {"host":"machinedatanglobal.c4sty2dpq6yv.ap-northeast-1.rds.amazonaws.com",
#                       "user":"Nglobal_root_NIW",
#                       "password":"Niw_Machinedata_11089694",
#                       "db":"NEPOWER_1",
#                       "table":"dataparameter2",
#                       "port":3306}

SQL_SERVER_REALTIME    = {"host":"10.4.171.204",
                    "user":"root",
                    "password":"niw2082023",
                    "db":"omron",
                    "table":"omron_test",
                    "port":3306}
#SQL_SERVER_RECAP    = {"host":"10.4.171.204",
#                    "user":"root",
#                    "password":"niw2082023",
#                    "db":"omron",
#                    "table":"omron_recap",
#                    "port":3306}
SQL_TIMEOUT   = 3 # the maximum time this device will wait for completing MySQl query (in seconds)
SQL_INTERVAL  = 60 # the period between each subsequent update to database (in seconds)
FILENAME_REALTIME  = 'modbus_omron_realtime_log.csv'
FILENAME_RECAP     = 'modbus_omron_recap_log.csv'

# Socket communication parameters
UNIX_SOCKET_PATH = '/tmp/ipc_socket'   #AF_UNIX
INET_SOCKET_PATH = ('127.0.0.1', 9000) #AF_INET

#query.debugging()  # Monitor Modbus communication for debugging
QUEUE = Queue()

def setup_modbus():
    global PORT0, PORT1, METHOD, BYTESIZE, STOPBITS, PARITY, BAUDRATE, CLIENT_LATENCY, TIMEOUT
    # Set each Modbus communication port specification
    client0 = ModbusClient(port=PORT0, method=METHOD, stopbits=STOPBITS, bytesize=BYTESIZE, parity=PARITY, baudrate=BAUDRATE, timeout=TIMEOUT)
    #client1 = ModbusClient(port=PORT1, method=METHOD, stopbits=STOPBITS, bytesize=BYTESIZE, parity=PARITY, baudrate=BAUDRATE, timeout=TIMEOUT)
    # Connect to the Modbus serial
    client0.connect()
    #client1.connect()
    # Define the Modbus slave/server (nodes) objects
    ct1 = kmn1.node(slave=3, name='OMRON CT1', client=client0, delay=CLIENT_LATENCY, max_count=20, increment=2, shift=0)
    #ct2 = kmn1.node(slave=2, name='OMRON CT2', client=client0, delay=CLIENT_LATENCY, max_count=20, increment=2, shift=0)
    #ct3 = msystem.node(slave=1, name='MSYSTEM', client=client0, delay=CLIENT_LATENCY, max_count=20, increment=2, shift=2)
    #ct4 = km50.node(slave=4, name='KM50', client=client0, delay=CLIENT_LATENCY, max_count=20, increment=1, shift=0)
    #server = [ct1,ct2,ct3]
    server = [ct1]
    return server

def read_modbus(server):
    addr=[["Active_Power","Generated_Active_Energy_kWh","Voltage_1","Current_1"]#,
          #["Active_Power","Generated_Active_Energy_kWh","Voltage_2","Current_2"]
         ]
    
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
    
    title = ["DATE","TIME","現在発電量","累積発電量","発電機回転数","発電機電圧",
             "発電機電流","本日三相発電","ｶﾞｲﾄﾞﾍﾞﾝ開度","水圧","流量","効率","水位",
             "系統電圧","系統電流","系統連系　ｲﾝﾊﾞｰﾀ　異常保持","ｶﾞｲﾄﾞﾍﾞｰﾝｲﾝﾊﾞｰﾀ異常保持",
             "放電抵抗器　過熱異常保持","制動ﾕﾆｯﾄ　異常保持","発電機　過熱異常　保持",
             "発電機　ｲﾝﾊﾞｰﾀ　異常保持","発電機　運転","発電機　運転準備","系統連系　ｺﾝﾊﾞｰﾀ　運転",
             "系統連系　ｺﾝﾊﾞｰﾀ　運転準備","発電機電力","発電機電圧","ﾍﾞｱﾘﾝｸﾞ温度"
            ]
    
    data = [timer.strftime("%Y-%m-%d"),timer.strftime("%H:%M:%S"),
            (server[0].Active_Power*100),(server[0].Generated_Active_Energy_kWh*10),
            0,(server[0].Voltage_1*10),(server[0].Current_1*10),(0*1000),
            (0*100),(0*1000),(0*1),(0*100),(0*1),(0*10),(0*10),0,0,0,0,0,
            0,0,0,0,0,(0*10),(0*1),(0*10)
           ]
    
    return title, data

def update_SQL(title, data, timer, csv_file, sql_server, last_time, interval_upload=0, timeout=3):
    # Define MySQL queries and data which will be used in the program
    sql_query = ("INSERT INTO `{}` ({}) VALUES ({})".format(SQL_SERVER["table"],
                                                                ",".join(title),
                                                                ",".join(['%s' for _ in range(len(title))])))

    query.log_in_csv(title ,data, timer, csv_file)
    if (timer - last_time).total_seconds() > interval_upload:
        last_time = timer
        query.retry_mysql(sql_server, sql_query, csv_file, timeout)
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
                real_time = start
                recap_time = start
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
                #update_SQL(title, data, timer, FILENAME_REALTIME, SQL_SERVER_REALTIME, real_time, 0, SQL_TIMEOUT)
                #update_SQL(title, data, timer, FILENAME_RECAP, SQL_SERVER_RECAP, recap_time, 43200, SQL_TIMEOUT*144)
                query.update_FTP(title, data, timer, FILENAME_REALTIME, FTP_SERVER_REALTIME, real_time, 0, SQL_TIMEOUT)
                query.update_FTP(title, data, timer, FILENAME_RECAP, FTP_SERVER_RECAP, recap_time, 43200, SQL_TIMEOUT*144)
                
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
