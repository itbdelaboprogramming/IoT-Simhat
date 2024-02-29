"""
#title           :yaskawa_GA500.py
#description     :modbus library for Inverter YASKAWA GA500
#author          :Nicholas Putra Rihandoko
#date            :2023/05/13
#version         :0.1
#usage           :Energy Monitoring System
#notes           :
#python_version  :3.7.3
#==============================================================================
"""
import time

# FUNCTION CODE PYMODBUS SYNTAX
# 0x03 (3) = read_holding_registers(address, count, **kwargs); Read the Description of Holding Register
# 0x08 (8) = diagnostic_sub_request(sub_function_code, data, **kwargs); Loopback Test & sub-fc determines the exact sub-function you want to perform
# 0x10 (16) = write_registers(address, values, **kwargs); Writing to Multiple Holding Registers
# 0x5A (90) = CUSTOMIZED FUNCTION; Writing to Multiple Holding Registers / Reading the Register Indicated
#             0x10 + 0x03
# 0x67 (103) = has 2 subfunction code, CUSTOMIZED FUNCTION
#              0x010D () ; Reading Contents of Non-Consecutive Holding Registers
#              0x010E () ; Writing Contents of Non-Consecutive Holding Registers

# the memory addresses are in 1 hex increment

class node:
    def __init__(self,slave,name,client,delay=200,max_count=20,increment=1,shift=0):
        self._name                      = name
        self._slave                     = slave
        self._client                    = client
        self._client_transmission_delay = delay/1000    # in seconds
        self._max_count                 = max_count     # maximum read/write address count in a single command
        self._shift                     = shift         # address shift
        self._inc                       = increment     # address increment
        # Commands and memory address that are available/configured, add if needed
        self._memory_dict = {
            ## Read Operation Status Monitors
            "Frequency_Reference":      {"fcr":0x03, "fcw":None, "address":0x0040, "scale":1/100, "bias":0, "round":1}, # Hz
            "Output_Frequency":         {"fcr":0x03, "fcw":None, "address":0x0041, "scale":1/100, "bias":0, "round":1}, # Hz
            "Output_Current":           {"fcr":0x03, "fcw":None, "address":0x0042, "scale":0.7/100, "bias":0, "round":2}, # Amps, AC
            "Output_Voltage_Reference": {"fcr":0x03, "fcw":None, "address":0x0045, "scale":1/10, "bias":0, "round":1}, # Volts, AC
            "DC_Bus_Voltage":           {"fcr":0x03, "fcw":None, "address":0x0046, "scale":1, "bias":0, "round":1}, # Volts
            #"Output_Power":             {"fcr":0x03, "fcw":None, "address":0x0047, "scale":1, "bias":0, "round":1},
            "Output_Voltage":           {"fcr":0x03, "fcw":None, "address":0x154E, "scale":1/10, "bias":0, "round":1}, # Volts, AC
            "Motor_Speed":              {"fcr":0x03, "fcw":None, "address":0x0044, "scale":1/100, "bias":0, "round":1},
            "Torque_Ref":               {"fcr":0x03, "fcw":None, "address":0x0048, "scale":1/10, "bias":0, "round":0},
            ## Read Maintenance Monitors
            "Cum_Operation_Time":       {"fcr":0x03, "fcw":None, "address":0x004C, "scale":1, "bias":0, "round":0},
            "Num_of_Run_Cmd":           {"fcr":0x03, "fcw":None, "address":0x0075, "scale":1, "bias":0, "round":0},
            "Cooling_Fan_Ope_Time":     {"fcr":0x03, "fcw":None, "address":0x0067, "scale":1, "bias":0, "round":0},
            "Cool_Fan_Maintenance":     {"fcr":0x03, "fcw":None, "address":0x007E, "scale":1, "bias":0, "round":0},
            "Capacitor_Maintenance":    {"fcr":0x03, "fcw":None, "address":0x007C, "scale":1, "bias":0, "round":0},
            "Heatsink_Temperature":     {"fcr":0x03, "fcw":None, "address":0x0068, "scale":1, "bias":0, "round":0},
            ## Read PID Monitors
            "PID_Feedback":             {"fcr":0x03, "fcw":None, "address":0x0057, "scale":1/100, "bias":0, "round":2},
            "PID_Input":                {"fcr":0x03, "fcw":None, "address":0x0063, "scale":1/100, "bias":0, "round":2},
            "PID_Output":               {"fcr":0x03, "fcw":None, "address":0x0064, "scale":1/100, "bias":0, "round":2},
            "PID_Setpoint":             {"fcr":0x03, "fcw":None, "address":0x0065, "scale":1/100, "bias":0, "round":2},
            ## Read and Write various data type
            "Run_Command":              {"fcr":0x03, "fcw":0x10, "address":0x0001, "scale":1, "bias":0, "round":0, "param":0b0000000000000000},
            "Freq_Ref":                 {"fcr":0x03, "fcw":0x10, "address":0x0002, "scale":1, "bias":0, "round":0, "param":0x0000}, # check 0x0040
            "Output_Voltage_gain":      {"fcr":0x03, "fcw":0x10, "address":0x0003, "scale":1/10, "bias":0, "round":1, "param":0x0000},
            "Torque_Limit":             {"fcr":0x03, "fcw":0x10, "address":0x0004, "scale":1/10, "bias":0, "round":1, "param":0x0000},
            "Torque_Compensation":      {"fcr":0x03, "fcw":0x10, "address":0x0005, "scale":1/10, "bias":0, "round":1, "param":0x0000},
            "PID_Setpoint_X":           {"fcr":0x03, "fcw":0x10, "address":0x0006, "scale":1/10, "bias":0, "round":1, "param":0x0000}, # check 0x0065
            "MFDO_Setting":             {"fcr":0x03, "fcw":0x10, "address":0x0009, "scale":1, "bias":0, "round":0, "param":0b0000000000000000},
            "Pulse_Train_Output":       {"fcr":0x03, "fcw":0x10, "address":0x000A, "scale":1, "bias":0, "round":0, "param":0x0000},
            "Command_Selection_Set":    {"fcr":0x03, "fcw":0x10, "address":0x000F, "scale":1, "bias":0, "round":0, "param":0b0000000000000000},
            "Extended_Multifunc_Input": {"fcr":0x03, "fcw":0x10, "address":0x15C0, "scale":1, "bias":0, "round":0, "param":0b0000000000000000},

            "Time_Setting":             {"fcr":0x03, "fcw":0x10, "address":0x3004, "scale":1, "bias":0, "round":0, "param":0000},
            "Years_Day_Setting":        {"fcr":0x03, "fcw":0x10, "address":0x3005, "scale":1, "bias":0, "round":0, "param":0000},
            "Date_Setting":             {"fcr":0x03, "fcw":0x10, "address":0x3006, "scale":1, "bias":0, "round":0, "param":0000},
            "Set_Date_Info":            {"fcr":0x03, "fcw":0x10, "address":0x3007, "scale":1, "bias":0, "round":0, "param":0},
            }
        # Used to shift the Modbus memory address for some devices
        for key in self._memory_dict: self._memory_dict[key]["address"] += shift
        # Extra calculation for parameters/data that is not readily available from Modbus, add if needed
        self._extra_calc = {
            ## calculate
            "AC_Power":             {"scale":0.91*(3**(0.5))/1000, "bias":0, "round":1, "limit":[], "scale_dep":[[1,"Output_Current"],[1,"Output_Voltage"]], "bias_dep":[[0,"Output_Voltage"]]}, # kW
            "DC_Current_raw":       {"scale":0.91*(3**(0.5)), "bias":0, "round":3, "limit":[], "scale_dep":[[1,"Output_Current"],[1,"Output_Voltage"],[-1,"DC_Bus_Voltage"]], "bias_dep":[[0,"DC_Bus_Voltage"]]}, # Amps
            "DC_Current":           {"scale":-0.158, "bias":-17.81, "round":2, "limit":[0.3,0], "scale_dep":[[2,"DC_Current_raw"]], "bias_dep":[[-4.37/0.158,"DC_Current_raw"]]} # Amps
            } # Please insert scale_dep and bias_dep with parameter in memory_dict even it actaully its unnecessary, you can fill the constant == 0

    def reset_read_attr(self):
        # Reset (and/or initiate) object's attributes
        for attr_name, attr_value in vars(self).items():
            if not attr_name.startswith("_"): setattr(self, attr_name, 0)

    def map_read_attr(self,raw_address):
        # get the attribute data using its Modbus memory address
        mapped_addr = []
        for key, value in self._memory_dict.items():
            for a in raw_address:
                if value["address"] == a:
                    try: mapped_addr.append([key, getattr(self, key)])
                    except: print(" -- one or more mapped address has not been read from server --")
                    break
        return mapped_addr

    def handle_sign(self,register):
        # Handle negative byte values using 2's complement conversion
        signed_values = []
        for i, data in enumerate(register):
            if i % self._inc == 0:
                for b in range(self._inc-1,0,-1):
                    data = (data << 16) | register[i+b]
                if data == None: # For avoid error because of None data
                    signed_value = data
                elif data >= (0x8000 << (16*(self._inc-1))):
                    signed_value = -int((data ^ ((1 << (16*self._inc)) - 1)) + 1)
                else: signed_value = int(data)
                signed_values.append(signed_value)
            else: signed_values.append(None)
        return signed_values

    def get_compile_dimension(self,array):
        # Get nested array dimension/size
        dim = []
        if isinstance(array, list):
            dim.append(len(array))
            inner_dim = self.get_compile_dimension(array[0])
            if inner_dim: dim.extend(inner_dim)
        return dim
    
    def create_copy_of_compile(self,size):
        # Build nested array with certain dimension/size
        if len(size) == 1: return [None] * size[0]
        else: return [self.create_copy_of_compile(size[1:]) for _ in range(size[0])]
        
    def copy_value_to_compile(self, array, copy_array):
        # Copy attribute_value to new array based on the compile blueprint (self._extra_calc[key]["compile"])
        if isinstance(array, list):
            for i, item in enumerate(array):
                if isinstance(item, list):
                    self.copy_value_to_compile(item, copy_array[i])
                elif isinstance(item, str):
                    if hasattr(self, item):
                        copy_array[i] = getattr(self, item)

    def handle_extra_calculation(self):
        # Additional computation for self._extra_calc parameters
        for key, value in self._extra_calc.items():
            if self._extra_calc[key].get("compile") is not None:
                # Make a same size array, copy the the dependency to the new array, assign it to new attribute
                dim = self.get_compile_dimension(value["compile"])
                comp = self.create_copy_of_compile(dim)
                self.copy_value_to_compile(value["compile"], comp)
                setattr(self, key, comp)
            else:
                val = 1
                # Calculate the parameters, assign it to new attribute, skip if dependency not met
                try:
                    for scale in value["scale_dep"]:
                        if getattr(self, scale[1]) == None: # For avoid error because of None data
                            val = None
                        elif getattr(self, scale[1]) == 0:
                            val = 0 
                        else: val *= getattr(self, scale[1])**scale[0]
                    for bias in value["bias_dep"]:
                        if getattr(self, bias[1]) == None: # For avoid error because of None data
                            val = None
                        else:
                            val += bias[0]*getattr(self, bias[1])
                    if val != None:
                        val = round(val * value["scale"] + value["bias"], value["round"])
                        if value["limit"] and val:
                            if val < value["limit"][0]: val = value["limit"][1]
                    setattr(self, key, val)
                except AttributeError: pass

    def save_read(self,response,save):
        # Save responses to object's attributes
        s = 0
        for i, reg in enumerate(response):
            if s <= len(save)-1:
                if save[0].startswith('Hx'): start_save = int(save[0],16)
                else: start_save = self._memory_dict[save[0]]["address"]
                if save[s].startswith('Hx'):
                    if int(save[s],16) == start_save+i:
                        setattr(self, save[s], reg); s=s+1
                else:
                    if self._memory_dict[save[s]]["address"] == start_save+i:
                        if reg == None: # For avoid error because of None data
                            val = reg
                        else:
                            val = round(reg * self._memory_dict[save[s]]["scale"] + self._memory_dict[save[s]]["bias"], self._memory_dict[save[s]]["round"])
                        setattr(self, save[s], val); s=s+1

    def count_address(self,fcr,raw_address):
        # Configure the read address (final_addr) and the attribute name where the read value is saved (final_save)
        address, temp_addr, final_addr, save, temp_save, final_save = [], [], [], [], [], []

        # Match the address with the information in self._memory_dict library
        for key, value in self._memory_dict.items():
            if value["address"] in raw_address or key.lower() in raw_address:
                address.append(value["address"]); save.append(key)
                if fcr == None: fcr = value["fcr"]
                raw_address = [x for x in raw_address if (x != value["address"] and x != key.lower())]
                if not raw_address: break

        # If the address is not available in the library, then use it as is
        for a in raw_address:
            if isinstance(a,str):
                print(" -- unrecognized address for '{}' --".format(a))
            else:
                address.append(a); save.append('Hx'+hex(a)[2:].zfill(4).upper())
                print(" -- address '{}' may gives raw data, use with discretion --".format(save[-1]))

        # Divide the address to be read into several command based on max_count
        address, save = zip(*sorted(zip(address, save)))
        address, save = list(address), list(save)
        for i, a in enumerate(address):
            if not temp_addr:
                temp_addr.append(a); temp_save.append(save[i])
            else:
                if a - temp_addr[0] + 1 <= self._max_count:
                    temp_addr.append(a); temp_save.append(save[i])
                else:
                    final_addr.append(temp_addr); final_save.append(temp_save)
                    temp_addr, temp_save = [a], [save[i]]
        if temp_addr: final_addr.append(temp_addr); final_save.append(temp_save)
        return fcr, final_addr, final_save

    def reading_sequence(self,fcr,address):
        response = None
        fcr, addr, save = self.count_address(fcr,address)            
        # Send the command and read response with function_code 0x03 (3) or 0x04 (4)
        for i, a in enumerate(addr):
            if fcr == 0x03:
                try:
                    response = self._client.read_holding_registers(address=a[0], count=a[-1]-a[0]+self._inc, slave=self._slave)
                    self.save_read(self.handle_sign(response.registers),save[i])
                except: # For avoid error because of None data
                    dummy_registers = [None]*(a[-1]-a[0]+self._inc) #len(addr)
                    self.save_read(self.handle_sign(dummy_registers), save[i])
                time.sleep(self._client_transmission_delay)
            elif fcr == 0x04:
                try:
                    response = self._client.read_input_registers(address=a[0], count=a[-1]-a[0]+self._inc, slave=self._slave)
                    self.save_read(self.handle_sign(response.registers),save[i])
                except: # For avoid error because of None data
                    dummy_registers = [None]*(a[-1]-a[0]+self._inc) #len(addr)
                    self.save_read(self.handle_sign(dummy_registers), save[i])
                time.sleep(self._client_transmission_delay)
            else: print(" -- function code needs to be declared for this list of read address --")
        self.handle_extra_calculation()
        return response
            
        #if fcr == 0x03:
        #    for i, a in enumerate(addr):
        #        try:
        #            response = self._client.read_holding_registers(address=a[0], count=a[-1]-a[0]+self._inc, slave=self._slave)
        #            self.save_read(self.handle_sign(response.registers),save[i])
        #        except:
        #            dummy_registers = [0]*len(addr)
        #            self.save_read(self.handle_sign(dummy_registers), save[i])
        #        time.sleep(self._client_transmission_delay)
        #    
        #elif fcr == 0x04:
        #    for i, a in enumerate(addr):
        #        try:
        #            response = self._client.read_input_registers(address=a[0], count=a[-1]-a[0]+self._inc, slave=self._slave)
        #            self.save_read(self.handle_sign(response.registers),save[i])
        #        except:
        #            dummy_registers = [0]*len(addr)
        #            self.save_read(self.handle_sign(dummy_registers), save[i])
        #        time.sleep(self._client_transmission_delay)
        #        
        #else: print(" -- function code needs to be declared for this list of read address --")
        #self.handle_extra_calculation()
        #return response

    def handle_multiple_writting(self,param):
        # convert parameter input into hexadecimal format based on address increment
        if param < 0: hex_param = hex((abs(param) ^ ((1 << (16*self._inc)) - 1)) + 1)[2:].zfill(4*self._inc)
        else: hex_param = hex(param)[2:].zfill(4*self._inc)
        values = [int(hex_param[i:i+4], 16) for i in range(0, 4*self._inc, 4)]
        return values

    def writting_sequence(self,fcw,address,param):
        response = None
        if isinstance(param, list):
            params = []
            for p in param: params.extend(self.handle_multiple_writting(p))
        else: params = self.handle_multiple_writting(param)
        # Send the command with function_code 0x06 (6) or 0x10 (16)
        if fcw == 0x06:
            response = self._client.write_register(address=address, value=param, slave=self._slave)
        elif fcw == 0x10:
            response = self._client.write_registers(address=address, values=params, slave=self._slave)
        time.sleep(self._client_transmission_delay)
        return response

    def handle_dependency(self,raw_address):
        # create list of read address based on the dependent parameters in self._extra_calc
        result = []
        for item in raw_address:
            if isinstance(item, list):
                result.extend(self.handle_dependency(item))
            else:
                if self._extra_calc.get(item):
                    for d in self._extra_calc.get(item)["scale_dep"]:
                        result.append(d[1].lower())
                    for d in self._extra_calc.get(item)["bias_dep"]:
                        result.append(d[1].lower())
                else: result.append(item.lower())
        return result

    def send_command(self,command,address,param=None,fc=None):
        response = None
        # Send the command and read response with function_code 0x03 (3) or 0x04 (4)
        if command == "read":
            fcr = fc
            address = [a.lower() if isinstance(a,str) else (a + self._shift) for a in address]
            for key, value in self._extra_calc.items():
                if key.lower() in address:
                    try: extra = self.handle_dependency(self._extra_calc[key]["compile"])
                    except KeyError: extra = self.handle_dependency([key])
                    address.extend(extra); address.remove(key.lower())
            response = self.reading_sequence(fcr, address)

        # start writting sequence to send command with function_code 0x06 (6) or 0x10 (16)
        elif command == "write":
            fcw = fc
            if not isinstance(address,str): address += self._shift
            for key, value in self._memory_dict.items():
                if value["address"] == address or key.lower() == str(address).lower():
                    address = value["address"]
                    if fcw == None:
                        fcw = value["fcw"]
                        if value["fcw"] == None:
                            print(" -- This address is read-only -- ")
                    if param == None:
                        if self._memory_dict[key].get("param") is not None:
                            param = value["param"]
                        else:
                            print(" -- no parameter to be written --"); return
                    else:
                        if self._memory_dict[key].get("scale") is not None:
                            param = param*value["scale"]
                    break
            
            if (fcw == None) or (param == None) or isinstance(address,str):
                print(" -- incomplete input argument -- ")
            else:
                response = self.writting_sequence(fcw, address, param)
                print("{} ({}) get: {}".format(key, str(hex(address)), response))

        else: print("-- unrecognized command --")
