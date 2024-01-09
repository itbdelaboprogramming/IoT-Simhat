"""
#title           :starter.py
#description     :IoT key feature scheduling script, used to start the main scripts on scheduled interval
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
import psutil

def kill_starter(pid):
    if pid == None:
        print('The script auth.py is currently not running')
    else:
        os.system('sudo kill {}'.format(pid))
        print('Successfully kill auth.py script')

def main_starter():
    pid = None
    # Find the process ID (PID) of the python script
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'python3' and 'auth.py' in ' '.join(process.cmdline()):
            pid = process.info['pid']
            break

    # To stop the auth.py script, uncomment this line below
    # kill_starter(pid); return

    # If the process ID (PID) of auth.py was not found, run the script
    if pid:
        print("The script auth.py is already running.")

        # Check whether the jobs are already running
        os.system('python3 {}/{} start'.format(os.path.dirname(os.path.abspath(__file__)),'auth.py'))

    else:
        # If auth.py is not already running, execute the script
        os.system('python3 {}/{} monitor'.format(os.path.dirname(os.path.abspath(__file__)),'auth.py'))

        print("Successfully run auth.py script.")
    print("")
    return pid

##=================== =================== Starter Routine =================== ===================##

main_starter()

# If you want to skip the authentication process, comment the line 'main_starter()', then uncomment this line bellow
#os.system('python3 {}/{} run'.format(os.path.dirname(os.path.abspath(__file__)),'src/jobs.py'))

# Run backup procedure, uncomment if needed
#os.system('python3 {}/{}'.format(os.path.dirname(os.path.abspath(__file__)),'backup.py'))