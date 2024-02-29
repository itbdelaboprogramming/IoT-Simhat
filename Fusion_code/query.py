"""
#title           :query.py
#description     :custom functions for PyMySQL ant others
#author          :Nicholas Putra Rihandoko
#date            :2023/07/27
#version         :0.1
#usage           :Python programming
#notes           :
#python_version  :3.7.3
#==============================================================================
"""

import logging
import pymysql
import signal
import datetime
import ftplib
import csv
import os

#################################################################################################################
# General function for debugging

def debugging():
    # Print the python library's process log for troubleshooting
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

def handle_timeout(signum, frame):
    raise TimeoutError("Execution timed out")
signal.signal(signal.SIGALRM, handle_timeout)

def get_cpu_temperature():
    # Read CPU temperature from file
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        temp = round(float(f.read().strip())/1000,1)
    return temp

def print_response(server,timer):
    cpu_temp = get_cpu_temperature()
    #return
    # Print the object's attribute, uncomment as needed
    for i in range(len(server)):
        print(server[i]._name, "MEASUREMENTS")
        print("Time             :", timer.strftime("%d/%m/%Y-%H:%M:%S"))
        print("CPU Temperature  :", cpu_temp, "degC")
        for attr_name, attr_value in vars(server[i]).items():
            if not attr_name.startswith("_"):
                if not isinstance(attr_value, list):
                    print(attr_name, "=", attr_value)
                else:
                    #continue
                    if not isinstance(attr_value[0], list):
                        print(attr_name, "=", attr_value)
                    else:
                        for i in range(len(attr_value)):
                            print(attr_name, i+1, "=", attr_value[i])
        print("")

#################################################################################################################
## Handle saving data to CSV

# Define the directory of the backup file and the data to be logged
log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save')
log_limit = 31

def strval(array):
    # Change an array into a string (used to save array value into MySQL database or CSV)
    string = " ".join(map(str, array))
    return string

def log_in_csv(title,data,timer,filename):
    global log_directory, log_limit
    #return
    file_directory = os.path.join(log_directory,filename)
    file_exists = True
    file_empty = True
    expired_rows_to_delete = None
    # Check if the file already exist or not
    try:
        with open(file_directory, 'r') as file:
            file_empty = not file.read(1)
            csv_log = list(csv.reader(file))
        # Read the line in the CSV file
        for row, row_data in enumerate(csv_log):
            if row > 0:
                csv_date = row_data[0]
                is_valid_date = True
                try: datetime.datetime.strptime(csv_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    csv_date = row_data[0] + ' ' + row_data[1]
                    try:
                        datetime.datetime.strptime(csv_date, '%Y-%m-%d %H:%M:%S')
                    except ValueError: is_valid_date = False
                if is_valid_date:
                    # Calculate the difference in days
                    log_date = datetime.datetime.strptime(csv_date, '%Y-%m-%d %H:%M:%S')
                    # Calculate how long has the data been logged
                    timediff = (timer - log_date).days
                    if timediff > log_limit: expired_rows_to_delete.append(row)
                    else: break
    except FileNotFoundError: file_exists = False
    # Remove the expired row then write the updated contents to a new CSV file
    if expired_rows_to_delete:
        csv_log = [row_data for row, row_data in enumerate(csv_log) if row not in expired_rows_to_delete]
        with open(file_directory, 'w') as file:
            writer = csv.writer(file)
            writer.writerows(csv_log)
    # Add new data into csv file ()
    with open(file_directory, mode='a' if file_exists else 'w', newline='') as file:
        line = csv.writer(file, delimiter =',')
        if file_empty: line.writerow(title)
        data = [strval(d) if isinstance(d,list) else d for d in data]
        line.writerow(data)

#################################################################################################################
## Interacting with MySQL Database

def connect_mysql(mysql_server,mysql_query,data=None,timeout=2):
    #return
    # Set the signal handler for the timeout
    signal.alarm(timeout)  # Start the timeout countdown
    try:
        # Setup Raspberry Pi as MySQl Database client
        with pymysql.connect(host=mysql_server["host"], user=mysql_server["user"], password=mysql_server["password"], db=mysql_server["db"], port=mysql_server["port"]) as db:
            # Write data in database
            if data:
                data = [strval(d) if isinstance(d,list) else d for d in data]
                db.cursor().execute(mysql_query,data)
                db.commit()
                val = True
                print("<===== Data is sent to database =====>")
                print("")
            else:
                with db.cursor() as read:
                    read.execute(mysql_query)
                    val = read.fetchall()
        # Reset the alarm as the query completed successfully
        signal.alarm(0)
        return val
    except TimeoutError as e:
        # Handle the timeout error
        print("problem with MySQL Server:")
        print(e)
        print("<===== ===== continuing ===== =====>")
        print("")
        return False
    except Exception as e:
        # Print the error message
        print("problem with MySQL Server:")
        print(e)
        print("<===== ===== continuing ===== =====>")
        print("")
        return False

def retry_mysql(mysql_server,mysql_query,filename,timeout=2):
    global log_directory
    #return
    file_directory = os.path.join(log_directory,filename)
    rows_to_delete = []
    # Check if the file already exist or not
    try:
        with open(file_directory, 'r') as file:
            csv_log = list(csv.reader(file))
        # Read the line in the CSV file
        for row, row_data in enumerate(csv_log):
            if row > 0:
                # Retry uploading the data to mysql
                upload_succeed = connect_mysql(mysql_server,mysql_query,row_data,timeout)
                if upload_succeed: rows_to_delete.append(row)
                else: break
    except FileNotFoundError: pass
    # Write the updated contents to a new CSV file
    if rows_to_delete:
        csv_log = [row_data for row, row_data in enumerate(csv_log) if row not in rows_to_delete]
        with open(file_directory, 'w') as file:
            writer = csv.writer(file)
            writer.writerows(csv_log)

def limit_db_rows(mysql_server,row_limit,timeout=2):
    mysql_query = ("DELETE FROM {} WHERE id NOT IN ( SELECT id FROM ( "
                       "SELECT id FROM {} ORDER BY id DESC LIMIT %s ) AS limited_rows )".format(
                           mysql_server["table"],mysql_server["table"]))
    connect_mysql(mysql_server,mysql_query,[row_limit],timeout)

#################################################################################################################
## Calculate uptime and downtime using MySQL

bootup_time = datetime.datetime.now()
def get_updown_time(mysql_server,timer,timeout=2):
    global bootup_time
    # Read the previous timestamps from database
    datetime_query = ("SELECT startup_date, startup_time, total_uptime, shutdown_date, shutdown_time, total_downtime, downtime FROM `{}` ORDER BY id DESC LIMIT 1".format(mysql_server["table"]))
    data_datetime = connect_mysql(mysql_server,datetime_query,timeout=timeout)
    if data_datetime:
        # Change the format into suitable timedate objects
        for data in data_datetime:
            prev_startup = datetime.datetime.combine(data[0], datetime.datetime.min.time()) + data[1]
            total_uptime = data[2]
            prev_update = datetime.datetime.combine(data[3], datetime.datetime.min.time()) + data[4]
            total_downtime = data[5]
            downtime = data[6]
    else:
        # In case of no previous data, initiate the values
        prev_startup = bootup_time
        total_uptime = datetime.timedelta(seconds=0)
        prev_update = timer
        total_downtime = datetime.timedelta(seconds=0)
        downtime = datetime.timedelta(seconds=0)
    # calculate the time difference and culmulative period from the timestamps
    uptime = (timer - bootup_time)
    if abs(bootup_time - prev_startup) < datetime.timedelta(seconds=60):
        total_uptime = total_uptime + abs(timer - prev_update)
    else:
        downtime = abs(bootup_time - prev_update)
        total_downtime = total_downtime + downtime
    return [bootup_time, uptime, total_uptime, downtime, total_downtime]

#################################################################################################################
## Handle Upload csv files using FTP

def upload_file_ftp(server, username, password, local_path, remote_path):
    try:
        with ftplib.FTP(server, username, password) as ftp:
            ftp.set_pasv(True)  # Use passive mode; change to False to try active mode
            with open(local_path, 'rb') as local_file:
                ftp.storbinary(f'STOR {remote_path}', local_file)
            print(f"Uploaded {local_path} to {remote_path}")
            return True
    except Exception as e:
        print(f"Error uploading {local_path}: {e}")
        return False
        
def download_file_ftp(server, username, password, remote_path, local_path):
    try:
        with ftplib.FTP(server, username, password) as ftp:
            ftp.set_pasv(True)  # Use passive mode; change to False to try active mode
            with open(local_path, 'wb') as local_file:
                ftp.retrbinary(f'RETR {remote_path}', local_file.write)
            print(f"Downloaded {remote_path} to {local_path}")
            return True
    except Exception as e:
        print(f"Error downloading {remote_path}: {e}")
        return False

def archive_file(file_path):
    try:
        archive_path = file_path + ".bak"
        os.rename(file_path, archive_path)
        print(f"Archived {file_path} to {archive_path}")
    except Exception as e:
        print(f"Error Archiving {file_path}: {e}")

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Deleted {file_path}")
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")

def prepare_new_file(file_path, header):
    try:
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)
        print(f"Created {file_path}")
    except Exception as e:
        print(f"Error creating {file_path}: {e}")

def key_check(dictionary, key):
    try:
        # Attempt to access the value
        value = dictionary[key]
        return value
    except KeyError:
        # Key does not exist
        print(f"'{key}' does not exist in the dictionary'")

def update_FTP(title, data, timer, filename, ftp_server, last_time, interval_upload=0, timeout=3):
    global log_directory
    server = key_check(ftp_server, 'host')
    username = key_check(ftp_server, 'user')
    password = key_check(ftp_server, 'password')
    path = key_check(ftp_server, 'path')
    remote_path = os.path.join(path,filename)
    local_path = os.path.join(log_directory,filename)
    log_in_csv(title ,data, timer, filename)
    if (timer - last_time).total_seconds() > interval_upload:
        last_time = timer
        if upload_file_ftp(server, username, password, local_path, remote_path):
            delete_file(local_path)
            prepare_new_file(local_path, title)

def update_SQL(title, data, timer, csv_file, sql_server, last_time, interval_upload=0, timeout=3):
    # Define MySQL queries and data which will be used in the program
    sql_query = ("INSERT INTO `{}` ({}) VALUES ({})".format(sql_server["table"],
                                                                ",".join(title),
                                                                ",".join(['%s' for _ in range(len(title))])))

    log_in_csv(title ,data, timer, csv_file)
    if (timer - last_time).total_seconds() > interval_upload:
        last_time = timer
        retry_mysql(sql_server, sql_query, csv_file, timeout)
