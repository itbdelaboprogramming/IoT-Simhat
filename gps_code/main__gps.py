"""
#title           :main__gps.py
#description     :
#author          :Nicholas Putra Rihandoko
#date            :2023/05/08
#version         :0.1
#usage           :
#notes           :
#python_version  :3.7.3
#==============================================================================
"""

# Import library
import datetime
import time
import query
import socketio
import json
import os
import sys

# Define GPS port
if sys.argv[1] == "SIM7600":
    from lib import SIM7600_GNSS as gnss
    port_id = 'SimTech__Incorporated_SimTech__Incorporated_0123456789ABCDEF-if02' # for SIM7600 GPS module
elif sys.argv[1] == "SE100":
    from lib import SE100_GNSS as gnss
    port_id = '/dev/ttyAMA0' # for SE100 GPS module using RaspberryPi's RX-TX (UART) pinout
elif sys.argv[1] == "Prolific":
    port_id = 'usb-Prolific_Technology_Inc._USB-Serial_Controller' # for GPS module using USB-to-TTL adaptor
else:
    port_id = 'usb-1a86_USB2.0-Serial-if00-port0' # for GPS module using USB-to-TTL adaptor
gps_port = os.popen('sudo bash {}/get_usb.bash {}'.format(os.path.dirname(os.path.abspath(__file__)), port_id)).read().strip()

interval        = 1 # the period between each subsequent communication routine/loop (in seconds)

# NIW REF = 33.2108277, 130.0459166
# ITB REF = -6.889777, 107.608666
# Define SocketIO  parameters
sio_server = "http://localhost:3000"
sio_payload = {"id": 1,
                "data": {
                    "latitude": 33.2108277,
                    "longitude": 130.0459166,
                    "status": "GPS Not Ready",
                    "vehicleName": "Car A"
                }}

#debug.debugging()
init = True  # variable to check modbus & mysql initialization
sio = socketio.Client()

@sio.event
def connect():
    sio.emit("init","Connection Established")
    print("Connection Established")

@sio.event
def disconnect():
    print("Disconnected")

# Checking the GPS connection
while init:
    try:
        gps = gnss.node(gps_port, sio_payload["data"]["vehicleName"])
        sio.connect(sio_server)
        print("<===== GPS Initialized =====>")
        print("")
        init = False

    except Exception as e:
        # Print the error message
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)

# Main loop
start = datetime.datetime.now() # time counter
while not init:
    try:
        # Send the command to read the measured value
        timer = datetime.datetime.now()
        gps.read_gps()

        # Send to the Socket.IO server
        try:
            sio_payload["data"]["latitude"] = gps.Latitude
            sio_payload["data"]["longitude"] = gps.Longitude
            sio_payload["data"]["status"] = gps.Status
            sio.emit("gps",json.dumps(sio_payload))
        except Exception as e:
            # Handle incoming events or perform other operations
            print(f'Error connecting to Socket.IO server: {e}')

        time.sleep(interval)

    except Exception as e:
        # Print the error message
        print(e)
        print("<===== ===== retrying ===== =====>")
        print("")
        time.sleep(3)
