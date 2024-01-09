"""
#title           :jobs.py
#description     :IoT key's lists of script to be monitored
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
import psutil
import subprocess

# Specify the path to the job list
jobs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'jobs.txt')

def run():
    print("")
    # Find the process ID (PID) of the python script
    with open(jobs_path, 'rb') as file:
        for line in file:
            jobs = line.rstrip().decode().split(' ')
            pid = None
            for process in psutil.process_iter(['pid', 'name']):
                # Check if the process name matches and if the script path is part of the command line arguments
                #if process.info['name'] == jobs[0] and os.path.basename(jobs[1]) in ' '.join(process.cmdline()):
                if process.info['name'] == jobs[0] and any(jobs[1] in cmd for cmd in process.cmdline()):
                    pid = process.info['pid']
                    print(process.info)
                    break
            # If the process ID (PID) was not found, run the process
            if pid:
                print("The job {} is already running.".format(os.path.basename(jobs[1])))
            else:
                command = ' '.join(jobs)
                os.system(command)
                print("Successfully run the job: {}".format(os.path.basename(jobs[1])))
            print("")

def kill():
    print("")
    # Find the process ID (PID) of the python script
    with open(jobs_path, 'rb') as file:
        for line in file:
            jobs = line.rstrip().decode().split(' ')
            pid = None
            for process in psutil.process_iter(['pid', 'name']):
                #if process.info['name'] == jobs[0] and os.path.basename(jobs[1]) in ' '.join(process.cmdline()):
                if process.info['name'] == jobs[0] and any(jobs[1] in cmd for cmd in process.cmdline()):
                    pid = process.info['pid']
                    break

             # If the process ID (PID) was found, terminate the process
            if pid:
                subprocess.run(['sudo', 'kill', str(pid)])
                print("Successfully kill the job: {}".format(os.path.basename(jobs[1])))
            else:
                print("The job {} is not running.".format(os.path.basename(jobs[1])))
            print("")
try:
    if sys.argv[1] == "run":
        run()
    elif sys.argv[1] == "kill":
        kill()
except:
    pass
