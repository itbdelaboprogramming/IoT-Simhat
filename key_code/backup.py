"""
#title           :backup.py
#description     :IoT key feature data logging/backup script, used to backup csv data from other brograms
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
import shutil
import pyzipper

# Specify the path to the USB drive and the filename
code_path = os.path.dirname(os.path.abspath(__file__))
backup_path = os.path.join(code_path,'src')
jobs_path = os.path.join(backup_path,'jobs.txt')
status_path = os.path.join(backup_path,'status.txt')
keyword_path = os.path.join(backup_path, 'keyword.txt')
zip_path = os.path.join(code_path,'iot_save.zip')

def copy_csv_files(source_dir, destination_dir):
    # Get the list of CSV files in the source directory
    csv_files = [file for file in os.listdir(source_dir) if file.endswith('.csv')]

    # Create the destination directory if it doesn't exist
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Copy each CSV file to the destination directory
    for csv_file in csv_files:
        source_path = os.path.join(source_dir, csv_file)
        destination_path = os.path.join(destination_dir, csv_file)
        shutil.copy(source_path, destination_path)

def compress_backup():
    # Compress the folder to a ZIP file with password
    with open(keyword_path, 'r') as file:
        password = file.read()
    output_path = zip_path
    source_path = os.path.join(backup_path,'save')
    with pyzipper.AESZipFile(output_path, "w",
                            compression=pyzipper.ZIP_STORED,
                            encryption=pyzipper.WZ_AES) as zipf:
        zipf.setpassword(password.encode())
        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=os.path.relpath(file_path,source_path))
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                zipf.write(dir_path, arcname=os.path.relpath(dir_path,source_path))

def compile_all_csv():
    # Copy all the csv files from the directories in jobs.txt list into one folder
    with open(jobs_path, 'rb') as file:
        for line in file:
            source_dir = os.path.join(line.rstrip().decode().split(' ')[1],'save')
            destination_dir = os.path.join(backup_path,'save',os.path.basename(os.path.dirname(source_dir)))
            copy_csv_files(source_dir, destination_dir)

def copy_to_usb():
    # Read the keyword inside the usb_path
    with open(status_path, 'r') as file:
        status = file.read() 
        if status == "1":
            usb_path = os.popen('bash {}/get_usb.bash'.format(backup_path)).read().strip()
            shutil.copy(zip_path, usb_path)        

##=================== =================== Backup Routine =================== ===================##

try:
    compile_all_csv()
except:
    pass

try:
    compress_backup()
except:
    pass

try:
    copy_to_usb()
except:
    pass