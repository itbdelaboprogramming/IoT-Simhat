"""
#title           :frame_es.py
#description     : Create Class for Energy Storage Frame for NePower Monitoring
#author          :Nauval Chantika
#date            :2023/09/25
#version         :1.0
#usage           :Energy Monitoring System, RS-485 and RS-232C interface
#notes           :
#python_version  :3.11.5
#==============================================================================
"""
import os
import socket
import threading
import tkinter as tk
from tkinter import ttk, font
from queue import Queue

# Constants
THEME_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
THEME_PATH = os.path.join(THEME_DIR_PATH, 'theme', 'Azure-ttk-theme', 'azure.tcl')
UNIX_SOCKET_PATH = '/tmp/ipc_socket'
INET_SOCKET_PATH = ('localhost', 9000)
QUEUE = 5
INTERVAL = 15  # in seconds for the socket timeout
BUFFER_SIZE = 1024
DEFAULT_DATA = ["none" for _ in range(19)]
QUEUE = Queue()

class StorageFrame(ttk.Frame):
    def __init__(self, master, data, frame_type='Default'): # If there are other arguments: (self, master, arg5, arg6)
        super().__init__(master)
        # All setup nad initial command
        self.clss = master

        #______________________________________________

        # Register all arguments another master in here
        #self.arg5 = arg5
        #self.arg6 = arg6
        self.data = data
        #______________________________________________

        # Register all variable you need to make widgets here
        self.time_vars = tk.StringVar()
        self.com_vars = []
        self.label_texts = []

        #______________________________________________

        # Register/Call all functions that is needed to run automatically
        self.frame_configuration()
        self.frame_type = frame_type
        self.create_widgets(data)

        #______________________________________________

        for i in range(5):
            self.grid_columnconfigure(i, weight=1)
        self.grid_rowconfigure(1, weight=1)

    # List of Function start from here
    def create_widgets(self, data):
        # Make widgets here
        time_label = tk.Label(self, textvariable=self.time_vars, font=('Helvetica', 10), anchor='w')
        Img_labels = tk.Label(self, text="BMS Schematics Right Here", font=font.Font(family='Helvetica', size=10, weight= 'bold'), bg= "#d90429")

        time_label.grid(row=0, column=0, sticky='news')
        Img_labels.grid(row=1, column=2, pady=10, sticky='news')

        # Load the image use " Tkinter's 'PhotoImage' " or " Pillow Package "
        # Using PIL -----------If you want to use .jpg, Make sure install 'Pillow' package first: pip install Pillow
        #image_path = Image.open(file='path/to/file.jpg') # using PIL
        #schematics_img = ImageTk.PhotoImage(image_path)
        # Tkinter ------------ only work for .png and .gif
        #image_path = 'path/to/file.png'
        #schematics_img = tk.PhotoImage(file=image_path)
        
        #schematic_label = tk.Label(self, image=schematics_img)

        default_font_fg = self.master.option_get('foreground', 'black')

        for component, details in self.configuration[f'{self.frame_type}']['components'].items():
            vars_number = details['vars']
            labels_number = details['labels']
            vars = [tk.StringVar() for _ in range(vars_number)]
            labels = [
                tk.Label(self, 
                         textvariable=vars[i], 
                         font=('Helvetica', 15, 'bold' if i == 0 else 'normal'), 
                         fg= default_font_fg if i == 0 or (i % 2) == 1  else '#d90429',
                         justify= 'left' if i == 0 else 'center')
            for i in range(len(vars))
            ]
            row_header, column_header = labels_number[0]+1, labels_number[1]
            row_value, column_value = labels_number[0]+2, labels_number[1]
            for j, label in enumerate(labels):
                if j == 0:
                    label.grid(row=labels_number[0], column=labels_number[1], pady=10, sticky='ew')
                elif (j % 2) == 1:
                    label.grid(row=row_header, column=column_header, pady=10, sticky='ew')
                    column_header += 1
                else: #(i % 2 == 0)
                    label.grid(row=row_value, column=column_value, pady=10, sticky='ew')
                    column_value += 1
                if column_header == 5:
                    row_header += 2
                    column_header = 0
                if column_value == 5:
                    row_value += 2
                    column_value = 0
            self.com_vars.append(vars)

        # Update the text of the labels with the provided data
        self.update_frame_data(data)

    def update_frame_data(self, data): # Update labels with data
        # Layouting
        time_label_text = f"{data[0]}"
        
        for i, (component, details) in enumerate(self.configuration[f'{self.frame_type}']['components'].items()):
            parameters = details['parameters']
        
            # Directly set the main component name to com_vars
            if len(self.com_vars[i]) > 0:
                self.com_vars[i][0].set(f"{component} Parameter")
        
            # Set the parameter names and values
            for idx, (name, value) in enumerate(parameters):
                if (2*idx + 1) < len(self.com_vars[i]):
                    self.com_vars[i][2*idx + 1].set(name)
                    self.com_vars[i][2*idx + 2].set(f"{data[value]}")
                else:
                    print(f"Warning: com_vars[{i}] does not have a position for indices {2*idx + 1} and {2*idx + 2}.")

        # Store the update Layout
        self.time_vars.set(time_label_text)

    def frame_configuration(self):
        self.configuration = {
            'Default': {
                'schematic': 'path/to/file/BMS_Default.png',
                'components': {
                    'Converter': {
                        'vars': 9,
                        'labels': [2, 0],
                        'parameters': [
                            (f"AC Voltage (V)", 7),
                            (f"AC Current (A)", 8),
                            (f"AC Power (kW)", 12),
                            (f"DC Voltage (V)", 6)
                        ]
                    },
                    'Battery': {
                        'vars': 5,
                        'labels': [5, 0],
                        'parameters': [
                            (f"Total Voltage (V)", 4),
                            (f"Temperature (C)", 2)
                        ]
                    },
                    'Inverter': {
                        'vars': 9,
                        'labels': [8, 0],
                        'parameters': [
                            (f"AC Voltage (V)", 17),
                            (f"AC Current (A)", 16),
                            (f"Output Power (kW)", 18),
                            (f"AC Freq (Hz)", 15)
                        ]
                    }
                }
            }
        }

def socket_server_thread(data_queue):
    # Only for AF_UNIX step
    if os.path.exists(UNIX_SOCKET_PATH):
        os.remove(UNIX_SOCKET_PATH)
        print("Socket path exists. Removing...")
    
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    #server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:   
        server_socket.bind(UNIX_SOCKET_PATH)
        #server_socket.bind(INET_SOCKET_PATH)
        server_socket.listen()
        while True:
            conn, _ = server_socket.accept()
            with conn:
                while True:
                    data = conn.recv(BUFFER_SIZE).decode('utf-8')
                    if not data:
                        break
                    data_list = data.split(',')
                    data_queue.put(data_list)
    except socket.error as e:
        print(f"Error: socket setup failed. {e}")
        exit(1)  # Exit with an error code
    return server_socket

def update_frame_from_queue(data_queue, content_frame):
    while not data_queue.empty():
        data_list = data_queue.get_nowait()
        # Assuming you have a method in StorageFrame to update data
        content_frame.update_frame_data(data_list)
    content_frame.after(1000, lambda: update_frame_from_queue(data_queue, content_frame))

def main(root):
    content = StorageFrame(root, DEFAULT_DATA)
    content.grid(row=0, column=0, sticky='nsew')
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # Start the socket communication thread
    server_thread = threading.Thread(target=socket_server_thread, args=(QUEUE,), daemon=True)
    server_thread.start()

    # Schedule the first GUI update from the queue
    update_frame_from_queue(QUEUE, content)

    try:
        root.mainloop()
    finally:
        # Cleanup will happen here when mainloop exits
        server_sock.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("NePower Monitoring")
    root.geometry("1020x600")
    root.tk.call('source', THEME_PATH)
    root.tk.call('set_theme', 'dark')
    
    main(root)
