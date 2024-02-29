"""
#title           :yaskawa_D1000.py
#description     :modbus library for Converter YASKAWA D1000
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
# 0x03 (3) = read_holding_registers
# 0x04 (4) = read_input_registers
# 0x06 (6) = write_register
# 0x10 (16) = write_registers

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
            "Consumed_Power_GWh":       {"fcr":0x03, "fcw":None, "address":0x0820, "scale":1, "bias":0, "round":1},
            "Consumed_Power_MWh":       {"fcr":0x03, "fcw":None, "address":0x0821, "scale":1, "bias":0, "round":1},
            "Consumed_Power_kWh":       {"fcr":0x03, "fcw":None, "address":0x0822, "scale":1, "bias":0, "round":1},
            "Produced_Power_GWh":       {"fcr":0x03, "fcw":None, "address":0x0823, "scale":1, "bias":0, "round":1},
            "Produced_Power_MWh":       {"fcr":0x03, "fcw":None, "address":0x0824, "scale":1, "bias":0, "round":1},
            "Produced_Power_kWh":       {"fcr":0x03, "fcw":None, "address":0x0825, "scale":1, "bias":0, "round":1},
            "DC_Voltage_Command":       {"fcr":0x03, "fcw":None, "address":0x1080, "scale":1, "bias":0, "round":1}, # Volts
            "DC_Voltage_Feedback":      {"fcr":0x03, "fcw":None, "address":0x1081, "scale":1, "bias":0, "round":1}, # Volts
            "DC_Current":               {"fcr":0x03, "fcw":None, "address":0x1082, "scale":1/100, "bias":0, "round":1}, # Amps
            "AC_Voltage":               {"fcr":0x03, "fcw":None, "address":0x1083, "scale":1, "bias":0, "round":1}, # Volts
            "AC_Current":               {"fcr":0x03, "fcw":None, "address":0x1084, "scale":1/100, "bias":0, "round":1}, # Amps
            "DC_Power":                 {"fcr":0x03, "fcw":None, "address":0x1085, "scale":1/10, "bias":0, "round":1}, # kW
            "AC_Power":                 {"fcr":0x03, "fcw":None, "address":0x1086, "scale":1/10, "bias":0, "round":1}, # kW
            "AC_Frequency":             {"fcr":0x03, "fcw":None, "address":0x1087, "scale":1/10, "bias":0, "round":1}, # kW
            "AC_Current_Reference":     {"fcr":0x03, "fcw":None, "address":0x1088, "scale":1/100, "bias":0, "round":1}, # Amps
            "Power_Factor":             {"fcr":0x03, "fcw":None, "address":0x1089, "scale":1/100, "bias":0, "round":1},
            ## Read Maintenance Monitors
            "Dry_Elapsed_Time":         {"fcr":0x03, "fcw":None, "address":0x4C, "scale":1, "bias":0, "round":0},
            "RUN_Cmd_Counter":          {"fcr":0x03, "fcw":None, "address":0x75, "scale":1, "bias":0, "round":0},
            "Fan_Elapsed_Time":         {"fcr":0x03, "fcw":None, "address":0x67, "scale":1, "bias":0, "round":0},
            "Fan_Life_Mon":             {"fcr":0x03, "fcw":None, "address":0x7E, "scale":1, "bias":0, "round":0},
            "Cap_Life_Mon":             {"fcr":0x03, "fcw":None, "address":0x7C, "scale":1, "bias":0, "round":0},
            "ChgCirc_Life_Mon":         {"fcr":0x03, "fcw":None, "address":0x7D6, "scale":1, "bias":0, "round":0},
            "Heatsink_Temp":            {"fcr":0x03, "fcw":None, "address":0x68, "scale":1, "bias":0, "round":0},
            "Current_PeakHold":         {"fcr":0x03, "fcw":None, "address":0x7CF, "scale":1, "bias":0, "round":0},
            "Reference_Source":         {"fcr":0x03, "fcw":None, "address":0x7DA, "scale":1, "bias":0, "round":0},
            "Option_Freq_Ref":          {"fcr":0x03, "fcw":None, "address":0x7DC, "scale":1/100, "bias":0, "round":2},
            ## Write
            "Operation_Multifunc_Input":{"fcr":0x03, "fcw":0x10, "address":0x0001, "scale":1, "bias":0, "round":0, "param":0b0000000000000000},
            "Active_Current_Limit_Pos": {"fcr":0x03, "fcw":0x10, "address":0x0004, "scale":1/1000, "bias":0, "round":1, "param":0000},
            "Multifunc_Relay_Output":   {"fcr":0x03, "fcw":0x10, "address":0x0009, "scale":1, "bias":0, "round":0, "param":0b0000000000000000},
            "DC_Bus_Voltage_Ref":       {"fcr":0x03, "fcw":0x10, "address":0x000D, "scale":1, "bias":0, "round":0, "param":0},
            "Active_Current_Limit_Neg": {"fcr":0x03, "fcw":0x10, "address":0x000E, "scale":1/1000, "bias":0, "round":1, "param":0000},
            "Ana_Monitor_Opti_A03_Out1":{"fcr":0x03, "fcw":0x10, "address":0x001B, "scale":1, "bias":0, "round":0, "param":0x0000},
            "Ana_Monitor_Opti_A03_Out2":{"fcr":0x03, "fcw":0x10, "address":0x001C, "scale":1, "bias":0, "round":0, "param":0x0000},
            "Dig_Output_Opti_D03_Out":  {"fcr":0x03, "fcw":0x10, "address":0x001D, "scale":1, "bias":0, "round":0, "param":0b0},

            "run_command_select":       {"fcr":0x03, "fcw":0x10, "address":0x0181, "scale":1, "bias":0, "round":0, "param":0b0},
            "run_in_programming_mode":  {"fcr":0x03, "fcw":0x10, "address":0x0187, "scale":1, "bias":0, "round":0, "param":0b0},
            "enter_EEPROM":             {"fcr":None, "fcw":0x10, "address":0x0900, "param":0x0000}, # Enter command to write data in EEPROM (changes remain after shutdown, MAX:100000x)
            "enter_RAM":                {"fcr":None, "fcw":0x10, "address":0x0910, "param":0x0000} # Enter command to write data in RAM (changes are lost after shutdown)
            }
        # Used to shift the Modbus memory address for some devices
        for key in self._memory_dict: self._memory_dict[key]["address"] += shift
        # Extra calculation for parameters/data that is not readily available from Modbus, add if needed
        self._extra_calc = {
            # "Example":             {"scale":0.91*(3**(0.5))/1000, "bias":0, "round":1, "limit":[], "scale_dep":[[1,"ParameterA"],[1,"ParameterB"]], "bias_dep":[[0,"ParameterC"]]}
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
                        elif getattr(self, scale[1]) != 0:
                            val *= getattr(self, scale[1])**scale[0]
                        else: val = 0
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
