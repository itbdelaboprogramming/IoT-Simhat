"""
#title           :auth.py
#description     :IoT key feature main script, used for USB authentification
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

import os
import sys
import time
import pyudev
from cryptography.fernet import Fernet

# Specify the relevant directory path
class path:
    def __init__(self):
        code_path = os.path.dirname(os.path.abspath(__file__))
        self.usb_path = os.popen('bash {}/src/get_usb.bash'.format(code_path)).read().strip()
        self.encryptor_path = os.path.join(code_path, 'src/encryptor.txt')
        self.keyword_path = os.path.join(code_path, 'src/keyword.txt')
        self.iot_key_path = os.path.join(code_path, 'iot_key.txt')
        self.file_path = os.path.join(self.usb_path, 'iot_key.txt')
        self.jobs_path = os.path.join(code_path, 'src/jobs.txt')
        self.jobs_script = os.path.join(code_path, 'src/jobs.py')
        self.status_path = os.path.join(code_path, 'src/status.txt')
        

def encrypt_file(file_path, public_key):
    # Read the contents of the file
    with open(file_path, 'rb') as file:
        data = file.read()

    # Encrypt the contents using the given key
    f = Fernet(public_key)
    encrypted_data = f.encrypt(data)

    # Write the encrypted contents back to the file
    with open(file_path, 'wb') as file:
        file.write(encrypted_data)

def decrypt_file(file_path, private_key):
    # Read the encrypted contents of the file
    with open(file_path, 'rb') as file:
        encrypted_data = file.read()

    # Decrypt the contents using the given key
    f = Fernet(private_key)
    decrypted_data = f.decrypt(encrypted_data)

    # Write the decrypted contents back to the file
    with open(file_path, 'wb') as file:
        file.write(decrypted_data)

def create_key():
    dir = path()
    create_new = [True, True]    

    # Check existing keyword file
    if os.path.isfile(dir.keyword_path) and os.path.getsize(dir.keyword_path) > 0:
        print("Keyword already exist in", dir.keyword_path)
        user_input = input('Do you want to overwrite it? (y/n): ').lower()
        if user_input != 'y':
            create_new[0] = False
            # Read the keyword file
            with open(dir.keyword_path, 'rb') as file:
                iot_keyword = file.read()
            print("Using existing keyword in", dir.keyword_path)

    if create_new[0]:
        print("Type your new keyword:")
        iot_keyword = input('').encode()
        # Create the text file and write the keyword to it
        with open(dir.keyword_path, 'wb') as file:
            file.write(iot_keyword)
        print("New keyword created & saved in", dir.keyword_path)

    # Check existing encryptor file
    if os.path.isfile(dir.encryptor_path) and os.path.getsize(dir.encryptor_path) > 0:
        print("Encryption key already exist in", dir.encryptor_path)
        user_input = input('Do you want to overwrite it? (y/n): ').lower()
        if user_input != 'y':
            create_new[1] = False
            # Read the encryption key file
            with open(dir.encryptor_path, 'rb') as file:
                key = file.read()
            print("Using existing encryption key in", dir.encryptor_path)

    if create_new[1]:
        # Create the text file and write the encryption key to it
        key = Fernet.generate_key()
        with open(dir.encryptor_path, 'wb') as file:
            file.write(key)
        print("New encryption key created & saved in", dir.encryptor_path)

    with open(dir.iot_key_path, 'wb') as file:
        file.write(iot_keyword)
    encrypt_file(dir.iot_key_path, key)

    os.system('sudo cp -rf {} {} > /dev/null 2>&1'.format(dir.iot_key_path, dir.file_path))
    print("The USB has been configured as IoT Key for this machine")
    print("Password for zipfile: {}".format(iot_keyword.decode()))
    
def iot_start():
    dir = path()
    
    # Debugging section to check usb path
    print(dir.usb_path)
    # argu1 = os.path.exists(dir.usb_path)
    # argu2 = "devicenotfound" in dir.usb_path
    # print(argu1)
    # print(argu2)
    
    # Check if the USB drive is connected
    if os.path.exists(dir.usb_path) and not "devicenotfound" in dir.usb_path:
        # Check if the file exists
        if os.path.isfile(dir.file_path):

            
            # Obtain the encyption key from the code's directory
            with open(dir.encryptor_path, 'rb') as file:
                key = file.read().decode()

            # Decrypt the contents of the file
            decrypt_file(dir.file_path, key)
            
            # Read the keyword inside the usb_path
            with open(dir.file_path, 'rb') as file:
                content = file.read().decode()

            # Read the keyword inside the code_path
            with open(dir.keyword_path, 'rb') as file:
                keyword = file.read().decode()
            
            # Check if the keyword is present and correct
            if content == keyword and os.path.getsize(dir.file_path) > 0:
                # Run the python script
                os.system('lxterminal -e python3 {} run &'.format(dir.jobs_script))
                print("Successful authentication: IoT script is now running")

                # Write USB key status to be read by backup.py
                with open(dir.status_path, 'w') as file:
                    file.write("1")

                # Encrypt the contents of the file
                # encrypt_file(dir.file_path, key)
                return
            else:
                print("Failed authentication: wrong or empty keyword")
        else:
            print("Failed authentication: keyfile not found")
    else:
        print("USB key not connected")

    # Encrypt the contents of the file
    encrypt_file(dir.file_path, key)
    
    # Write USB key status to be read by backup.py
    with open(dir.status_path, 'w') as file:
        file.write("0")
    print("")

def iot_stop():
    dir = path()
    
    # Debugging section to check usb path
    print(dir.usb_path)
    # argu1 = os.path.exists(dir.usb_path)
    # argu2 = "devicenotfound" in dir.usb_path
    # print(argu1)
    # print(argu2)
    # print("")

    # Check if the USB drive is not connected
    if not os.path.exists(dir.usb_path) or "devicenotfound" in dir.usb_path:
        # Terminate the process in the jobs list
        os.system('python3 {} kill'.format(dir.jobs_script))
        # Write USB key status to be read by backup.py
        with open(dir.status_path, 'w') as file:
            file.write("0")
    else:
        # Write USB key status to be read by backup.py
        with open(dir.status_path, 'w') as file:
            file.write("1")
        print("USB key is still connected")
    print("")

def add_jobs():
    dir = path()
    print("Enter the command-line parameters")
    print("Only two arguments (interpreter & script's absolute directory)")
    print("Ex: python3 /directory/to/your_script.py")
    print("")
    interpreter = input("Interpreter: ")
    script = input("Script: ")
    with open(dir.jobs_path, 'a') as file:
        file.write(interpreter)
        file.write(" ")
        file.write(script)
        file.write("\n")
    print("")
    print("Job added on the list")

def list_jobs():
    dir = path()
    with open(dir.jobs_path, 'r') as file:
        for line in file:
            print(line.rstrip().split(' '))

def reset_jobs():
    dir = path()
    with open(dir.jobs_path, 'w') as file:
        file.write("")

##=================== Script Functions Based on Input Argument ===================##

print(sys.argv[1])
if sys.argv[1] == "monitor":
    # Create a context for monitoring
    context = pyudev.Context()

    # Create a monitor to watch for USB events
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='disk')

    # Monitor for USB drive events
    print("USB key monitoring service is now running ...")
    print("")
    iot_start()
    
    for action, device in monitor:
        try:
            time.sleep(3)
            if action == 'add':
                iot_start()
            if action == 'remove':
                iot_stop()
            print("USB key monitoring service is now running ...")
            print("")
        except:
            pass

# Generate IoT keyword & encryption files (initialize USB IoT Key system)
elif sys.argv[1] == "generate":
    dir = path()
    if not "devicenotfound" in dir.usb_path:
        create_key()
        
    else:
        print("Key generation is incomplete.")
        print("Please add an empty file named \"iot_key.txt\"")
        print(" in the USB drive that you want to configure as IoT Key,")
        print(" then try again.")
        print("")

# Check the existing keyword in the USB key
elif sys.argv[1] == "check":
    dir = path()
    if not "devicenotfound" in dir.usb_path:
        # read the encryption key in the machine
        with open(dir.encryptor_path, 'rb') as file:
            key = file.read().decode()
        try:
            # decrypt and print the keyword in the USB
            decrypt_file(dir.file_path, key)
            print("The IoT keyword saved inside the USB is:")
            with open(dir.file_path, 'rb') as file:
                print(file.read().decode())
            encrypt_file(dir.file_path, key)
        except BaseException as e:
            print("problem with -->",e)
        print("")
    else:
        print("Keyword check is incomplete.")
        print("Please plug-in the USB IoT Key and try again.")
        print("")
    
elif sys.argv[1] == "start":
    iot_start()

elif sys.argv[1] == "stop":
    iot_stop()

elif sys.argv[1] == "add_jobs":
    add_jobs()

elif sys.argv[1] == "list_jobs":
    list_jobs()

elif sys.argv[1] == "reset_jobs":
    reset_jobs()
    
else:
    pass
