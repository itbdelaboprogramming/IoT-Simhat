"""
#title           :omron_KMN1FLK.py
#description     :modbus library for OMRON KM-N1-FLK
#author          :Nicholas Putra Rihandoko, Nauval Chantika
#date            :2023/10/04
#version         :1.5
#usage           :Energy Monitoring System
#notes           :
#python_version  :3.11.6
#==============================================================================
"""
import time

# FUNCTION CODE PYMODBUS SYNTAX
# 0x03 (3) = read_holding_registers(address, count, **kwargs); Read the Description of Holding Register
# 0x06 (6) = write_register(address, value, **kwargs);
# 0x08 (8) = diagnostic_sub_request(sub_function_code, data, **kwargs); Loopback Test & sub-fc determines the exact sub-function you want to perform
# 0x10 (16) = write_registers(address, values, **kwargs); Writing to Multiple Holding Registers

# the memory addresses are in 2 hex increment

class node:
    def __init__(self,slave,name,client,delay=200,max_count=20,increment=2,shift=0):
        self._name                      = name
        self._slave                     = slave
        self._client                    = client
        self._client_transmission_delay = delay/1000    # in seconds
        self._max_count                 = max_count     # maximum read/write address count in a single command
        self._shift                     = shift         # address shift
        self._inc                       = increment     # address increment
        # Commands and memory address that are available/configured, add if needed
        self._memory_dict = {
            ## Read Instananeous Values
            "Voltage_1":                        {"fcr":0x03, "fcw":None, "address":0x0000, "scale":1/10, "bias":0, "round":1}, # Volts
            "Voltage_2":                        {"fcr":0x03, "fcw":None, "address":0x0002, "scale":1/10, "bias":0, "round":1}, # Volts
            "Voltage_3":                        {"fcr":0x03, "fcw":None, "address":0x0004, "scale":1/10, "bias":0, "round":1}, # Volts
            "Current_1":                        {"fcr":0x03, "fcw":None, "address":0x0006, "scale":1/1000, "bias":0, "round":2}, # Amps
            "Current_2":                        {"fcr":0x03, "fcw":None, "address":0x0008, "scale":1/1000, "bias":0, "round":2}, # Amps
            "Current_3":                        {"fcr":0x03, "fcw":None, "address":0x000A, "scale":1/1000, "bias":0, "round":2}, # Amps
            "Power_Factor":                     {"fcr":0x03, "fcw":None, "address":0x000C, "scale":1/100, "bias":0, "round":2},
            "Frequency":                        {"fcr":0x03, "fcw":None, "address":0x000E, "scale":1/10, "bias":0, "round":1}, # Hz
            "Active_Power":                     {"fcr":0x03, "fcw":None, "address":0x0010, "scale":1/10, "bias":0, "round":1}, # Watt
            "Reactive_Power":                   {"fcr":0x03, "fcw":None, "address":0x0012, "scale":1/10, "bias":0, "round":1}, # VAr
            "Consumed_Active_Energy_Wh":        {"fcr":0x03, "fcw":None, "address":0X0200, "scale":1, "bias":0, "round":0},
            "Generated_Active_Energy_Wh":       {"fcr":0x03, "fcw":None, "address":0x0202, "scale":1, "bias":0, "round":0},
            "Lead_Reactive_Energy_VArh":        {"fcr":0x03, "fcw":None, "address":0x0204, "scale":1, "bias":0, "round":0},
            "Lag_Reactive_Energy_VArh":         {"fcr":0x03, "fcw":None, "address":0x0206, "scale":1, "bias":0, "round":0},
            "Total_Reactive_Energy_VArh":       {"fcr":0x03, "fcw":None, "address":0x0208, "scale":1, "bias":0, "round":0},
            "Consumed_Active_Energy_kWh":       {"fcr":0x03, "fcw":None, "address":0x0220, "scale":1, "bias":0, "round":0},
            "Generated_Active_Energy_kWh":      {"fcr":0x03, "fcw":None, "address":0x0222, "scale":1, "bias":0, "round":0},
            "Lead_Reactive_Energy_kVArh":       {"fcr":0x03, "fcw":None, "address":0x0224, "scale":1, "bias":0, "round":0},
            "Lag_Reactive_Energy_kVArh":        {"fcr":0x03, "fcw":None, "address":0x0226, "scale":1, "bias":0, "round":0},
            "Total_Reactive_Energy_kVArh":      {"fcr":0x03, "fcw":None, "address":0x0228, "scale":1, "bias":0, "round":0},
            ## Read Maximum Values
            ## Read Minimum Values
            ## Read Total Power Consumption for Every 5 minute Period
            ## Read Total Power Consumption for Every 5 minutes
            ## Read Total Power Consumption for Every Hour
            ## Read Total Power Consumption for Every Day
            ## Read Spesific Power Consumption for Every Day
            ## Read Total Power Consumption for Every 5 minute Month
            ## Read Maximum Measurement Value for Every Day
            ## Read Minimum Measurement Value for Every Day

            ## Read and Write (Several Parameter still not registered yet, Please check the manual if you don't find what are you looking for)
            "set_Circuit_Apply":                {"fcr":None, "fcw":0x10, "address":0xF000, "scale":1, "bias":0, "round":0, "param":0x00000002},
            "shift_to_Setting":                 {"fcr":None, "fcw":0x06, "address":0xFFFF, "scale":1, "param":0x0700}, #0x0700 to setting, 0x0400 to measurement
            "shift_to_measurement":             {"fcr":None, "fcw":0x06, "address":0xFFFF, "scale":1, "param":0x0400}, #0x0700 to setting, 0x0400 to measurement
            "set_Phase_Wire_Config":            {"fcr":None, "fcw":0x10, "address":0x2000, "scale":1},
            "set_Unit_Number":                  {"fcr":None, "fcw":0x10, "address":0x2002, "scale":1},
            "set_Simple_Measurement":           {"fcr":None, "fcw":0x10, "address":0x200A, "scale":1},
            "set_Voltage_Simple_Measurement":   {"fcr":None, "fcw":0x10, "address":0x200C, "scale":10},
            "set_PF_Simple_Measurement":        {"fcr":None, "fcw":0x10, "address":0x200E, "scale":100},
            "set_Voltage_Assignment":           {"fcr":None, "fcw":0x10, "address":0x2012, "scale":1},
            "set_Server_Transmission_Delay":    {"fcr":None, "fcw":0x10, "address":0x220A, "scale":1},
            "set_Consumed_Active_Energy_Wh":    {"fcr":None, "fcw":0x10, "address":0x2600, "scale":1},
            "set_Generated_Active_Energy_Wh":   {"fcr":None, "fcw":0x10, "address":0x2602, "scale":1},
            "set_Lead_Reactive_Energy_VArh":    {"fcr":None, "fcw":0x10, "address":0x2604, "scale":1},
            "set_Lag_Reactive_Energy_VArh":     {"fcr":None, "fcw":0x10, "address":0x2606, "scale":1},
            "set_Total_Reactive_Energy_VArh":   {"fcr":None, "fcw":0x10, "address":0x2608, "scale":1},
            "set_Consumed_Active_Energy_kWh":   {"fcr":None, "fcw":0x10, "address":0x2620, "scale":1},
            "set_Generated_Active_Energy_kWh":  {"fcr":None, "fcw":0x10, "address":0x2622, "scale":1},
            "set_Lead_Reactive_Energy_kVArh":   {"fcr":None, "fcw":0x10, "address":0x2624, "scale":1},
            "set_Lag_Reactive_Energy_kVArh":    {"fcr":None, "fcw":0x10, "address":0x2626, "scale":1},
            "set_Total_Reactive_Energy_kVArh":  {"fcr":None, "fcw":0x10, "address":0x2628, "scale":1}
            }
        # Used to shift the Modbus memory address for some devices
        for key in self._memory_dict: self._memory_dict[key]["address"] += shift
        # Extra calculation for parameters/data that is not readily available from Modbus, add if needed
        self._extra_calc = {}

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
                if data >= (0x8000 << (16*(self._inc-1))):
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
                        if getattr(self, scale[1]) != 0:
                            val *= getattr(self, scale[1])**scale[0]
                        else: val = 0
                    for bias in value["bias_dep"]:
                        val += bias[0]*getattr(self, bias[1])
                    val = round(val * value["scale"] + value["bias"], value["round"])
                    if value["limit"]:
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
                except:
                    dummy_registers = [0]*(a[-1]-a[0]+self._inc) #len(addr)
                    self.save_read(self.handle_sign(dummy_registers), save[i])
                time.sleep(self._client_transmission_delay)
            elif fcr == 0x04:
                try:
                    response = self._client.read_input_registers(address=a[0], count=a[-1]-a[0]+self._inc, slave=self._slave)
                    self.save_read(self.handle_sign(response.registers),save[i])
                except:
                    dummy_registers = [0]*(a[-1]-a[0]+self._inc) #len(addr)
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
