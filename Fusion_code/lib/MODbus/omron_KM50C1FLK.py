"""
#title           :omron_KM50C1FLK.py
#description     :modbus library for OMRON KM50-C1-FLK
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
            "Voltage_2":                        {"fcr":0x03, "fcw":None, "address":0x0001, "scale":1/10, "bias":0, "round":1}, # Volts
            "Voltage_3":                        {"fcr":0x03, "fcw":None, "address":0x0002, "scale":1/10, "bias":0, "round":1}, # Volts
            "Current_1":                        {"fcr":0x03, "fcw":None, "address":0x0003, "scale":1/1000, "bias":0, "round":2}, # Amps
            "Current_2":                        {"fcr":0x03, "fcw":None, "address":0x0004, "scale":1/1000, "bias":0, "round":2}, # Amps
            "Current_3":                        {"fcr":0x03, "fcw":None, "address":0x0005, "scale":1/1000, "bias":0, "round":2}, # Amps
            "Power_Factor":                     {"fcr":0x03, "fcw":None, "address":0x0006, "scale":1/100, "bias":0, "round":2},
            "Frequency":                        {"fcr":0x03, "fcw":None, "address":0x0007, "scale":1/10, "bias":0, "round":1}, # Hz
            "Active_Power":                     {"fcr":0x03, "fcw":None, "address":0x0008, "scale":1/10, "bias":0, "round":1}, # Watt
            "Max_Active_Power":                 {"fcr":0x03, "fcw":None, "address":0x0009, "scale":1/100, "bias":0, "round":2}, # kW
            "React_Power":                      {"fcr":0x03, "fcw":None, "address":0x000A, "scale":1/10, "bias":0, "round":1}, # VAr
            "React_Power_kVAr":                 {"fcr":0x03, "fcw":None, "address":0x000B, "scale":1/100, "bias":0, "round":2}, # kVAr
            "Cons_Total_Energy_kWh":            {"fcr":0x03, "fcw":None, "address":0X000C, "scale":1/10, "bias":0, "round":1}, #kWh
            "Cons_Total_Energy_kgCO2":          {"fcr":0x03, "fcw":None, "address":0x000D, "scale":1/10, "bias":0, "round":1}, #kgCO2
            "Cons_Total_Energy_Wh":             {"fcr":0x03, "fcw":None, "address":0x001F, "scale":1, "bias":0, "round":0}, #Wh
            "Cons_Total_Active_GWh":            {"fcr":0x03, "fcw":None, "address":0x0020, "scale":1, "bias":0, "round":0}, #GWh
            "Cons_Total_Active_Wh":             {"fcr":0x03, "fcw":None, "address":0x0021, "scale":1, "bias":0, "round":0}, #Wh
            "Regene_Total_Energy_GWh":          {"fcr":0x03, "fcw":None, "address":0x0022, "scale":1, "bias":0, "round":0}, #GWh
            "Regene_Total_Energy_Wh":           {"fcr":0x03, "fcw":None, "address":0x0023, "scale":1, "bias":0, "round":0}, #Wh
            "Lead_Total_React_GVArh":           {"fcr":0x03, "fcw":None, "address":0x0024, "scale":1, "bias":0, "round":0}, #GVArh
            "Lead_Total_React_VArh":            {"fcr":0x03, "fcw":None, "address":0x0025, "scale":1, "bias":0, "round":0}, #VArh
            "Lagg_Total_React_GVArh":           {"fcr":0x03, "fcw":None, "address":0x0026, "scale":1, "bias":0, "round":0}, #GVArh
            "Lagg_Total_React_VArh":            {"fcr":0x03, "fcw":None, "address":0x0027, "scale":1, "bias":0, "round":0}, #VArh
            "Cons_Total_React_GVArh":           {"fcr":0x03, "fcw":None, "address":0x0028, "scale":1, "bias":0, "round":0}, #GVArh
            "Cons_Total_React_VArh":            {"fcr":0x03, "fcw":None, "address":0x0029, "scale":1, "bias":0, "round":0}, #VArh
            "Temperature":                      {"fcr":0x03, "fcw":None, "address":0x0038, "scale":1/10, "bias":0, "round":1}, #C or F
            "Conv_Mone_Cost_Upper":             {"fcr":0x03, "fcw":None, "address":0x0039, "scale":1, "bias":0, "round":0}, #Currency
            "Conv_Mone_Cost_lower":             {"fcr":0x03, "fcw":None, "address":0x003A, "scale":1, "bias":0, "round":0}, #Currency
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
            "set_Circuit_Apply":                {"fcr":0x03, "fcw":0x10, "address":0xF000, "scale":1, "bias":0, "round":0, "param":0x00000002},
            "set_Voltage_VT_Primary":           {"fcr":0x03, "fcw":0x10, "address":0xF001, "scale":1, "bias":0, "round":0, "param":0x00000000}, #V
            "set_Current_Rated_Primary":        {"fcr":0x03, "fcw":0x10, "address":0xF002, "scale":1, "bias":0, "round":0, "param":0x00000005},
            "set_Current_Lowcut":               {"fcr":0x03, "fcw":0x10, "address":0xF003, "scale":1/10, "bias":0, "round":1, "param":0x00000005}, #%
            "set_Pulse_Output_Unit":            {"fcr":0x03, "fcw":0x10, "address":0xF004, "scale":1, "bias":0, "round":0, "param":0x00000002}, #Wh
            "set_Display_Refresh_Unit":         {"fcr":0x03, "fcw":0x10, "address":0xF005, "scale":1, "bias":0, "round":0, "param":0x00000002},#s
            "set_Simple_Measurement":           {"fcr":0x03, "fcw":0x10, "address":0xF006, "scale":1, "bias":0, "round":0, "param":0x00000000}, 
            "set_Voltage_Simple_Measurement":   {"fcr":0x03, "fcw":0x10, "address":0xF007, "scale":1/10, "bias":0, "round":1, "param":0x00000064},#V
            "set_PF_Simple_Measurement":        {"fcr":0x03, "fcw":0x10, "address":0xF008, "scale":1/100, "bias":0, "round":2, "param":0x00000064}, 
            "set_Unit_Number":                  {"fcr":0x03, "fcw":0x10, "address":0xF009, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Baudrate":                     {"fcr":0x03, "fcw":0x10, "address":0xF00A, "scale":1, "bias":0, "round":0, "param":0x00000003}, # kbps
            "set_Data_Length":                  {"fcr":0x03, "fcw":0x10, "address":0xF00B, "scale":1, "bias":0, "round":0, "param":0x00000001}, # Default 00000000
            "set_Stop_Bits":                    {"fcr":0x03, "fcw":0x10, "address":0xF00C, "scale":1, "bias":0, "round":0, "param":0x00000000}, # Default 00000001
            "set_Vertical_Parity":              {"fcr":0x03, "fcw":0x10, "address":0xF00D, "scale":1, "bias":0, "round":0, "param":0x00000000}, # Default 00000002
            "set_Modbus_Timeout":               {"fcr":0x03, "fcw":0x10, "address":0xF00E, "scale":1, "bias":0, "round":0, "param":0x00000014}, # ms

            "set_Protection_Setting":           {"fcr":0x03, "fcw":0x10, "address":0xF00F, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Special_CT_Type":              {"fcr":0x03, "fcw":0x10, "address":0xF010, "scale":1, "bias":0, "round":0, "param":0x00000001}, #Default 00000002
            "set_CO2_Coefficient":              {"fcr":0x03, "fcw":0x10, "address":0xF011, "scale":1/1000, "bias":0, "round":3, "param":0x00000183}, #kgCO2/kWh
            "set_Protocol_Select":              {"fcr":0x03, "fcw":0x10, "address":0xF012, "scale":1, "bias":0, "round":0, "param":0x00000001}, # Default 00000000
            "set_Count_Average":                {"fcr":0x03, "fcw":0x10, "address":0xF013, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Event_Input1_PNPN":            {"fcr":0x03, "fcw":0x10, "address":0xF015, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Event_Input2_PNPN":            {"fcr":0x03, "fcw":0x10, "address":0xF016, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Event_Input1_NONC":            {"fcr":0x03, "fcw":0x10, "address":0xF017, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Event_Input2_NONC":            {"fcr":0x03, "fcw":0x10, "address":0xF018, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Measurement_Start_Time":       {"fcr":0x03, "fcw":0x10, "address":0xF019, "scale":1, "bias":0, "round":0, "param":0x00000000}, # 0000HHMM; HH 00~17 MM 00~3B (00:00~23:59)
            "set_Measurement_End_Time":         {"fcr":0x03, "fcw":0x10, "address":0xF01A, "scale":1, "bias":0, "round":0, "param":0x0000183B}, # 0000HHMM; HH 00~18 MM 00~3B (00:01~24:00)

            "set_Active_Power_Alarm":           {"fcr":0x03, "fcw":0x10, "address":0xF020, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Active_Power_Alarm_Upp_Limit": {"fcr":0x03, "fcw":0x10, "address":0xF021, "scale":1/10, "bias":0, "round":1, "param":0x00000320}, #%
            "set_Active_Power_Alarm_Hysteresis":{"fcr":0x03, "fcw":0x10, "address":0xF022, "scale":1/10, "bias":0, "round":1, "param":0x00000032}, #%
            "set_Active_Power_Alarm_OFF_Delay": {"fcr":0x03, "fcw":0x10, "address":0xF023, "scale":1/10, "bias":0, "round":1, "param":0x0000001E}, #s
            "set_Cons_Total_Energy_Select":     {"fcr":0x03, "fcw":0x10, "address":0xF024, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Active_Power_Alarm_ON_Delay":  {"fcr":0x03, "fcw":0x10, "address":0xF026, "scale":1/10, "bias":0, "round":1, "param":0x00000000}, #s
            "set_Active_Power_Alarm_Low_Limit": {"fcr":0x03, "fcw":0x10, "address":0xF027, "scale":1/10, "bias":0, "round":1, "param":0x00000000}, #% Always set below the Up limit address: F021

            "set_Regene_Power_Alarm_Upp_Limit": {"fcr":0x03, "fcw":0x10, "address":0xF028, "scale":1/10, "bias":0, "round":1, "param":0x00000320}, #%
            "set_Regene_Power_Alarm_Hysteresis":{"fcr":0x03, "fcw":0x10, "address":0xF029, "scale":1/10, "bias":0, "round":1, "param":0x00000032}, #%
            "set_Regene_Power_Alarm_OFF_Delay": {"fcr":0x03, "fcw":0x10, "address":0xF02A, "scale":1/10, "bias":0, "round":1, "param":0x0000001E}, #s
            "set_Regene_Power_Alarm_ON_Delay":  {"fcr":0x03, "fcw":0x10, "address":0xF02B, "scale":1/10, "bias":0, "round":1, "param":0x00000000}, #s
            "set_Regene_Power_Alarm_Low_Limit": {"fcr":0x03, "fcw":0x10, "address":0xF02C, "scale":1/10, "bias":0, "round":1, "param":0x00000000},#% Always set below the Up limit address: F028

            "set_Current_Alarm_Upp_Limit":      {"fcr":0x03, "fcw":0x10, "address":0xF02D, "scale":1/10, "bias":0, "round":1, "param":0x0000044C}, #%
            "set_Current_Alarm_Hysteresis":     {"fcr":0x03, "fcw":0x10, "address":0xF02E, "scale":1/10, "bias":0, "round":1, "param":0x00000032}, #%
            "set_Current_Alarm_OFF_Delay":      {"fcr":0x03, "fcw":0x10, "address":0xF02F, "scale":1/10, "bias":0, "round":1, "param":0x0000001E}, #s
            "set_Current_Alarm_ON_Delay":       {"fcr":0x03, "fcw":0x10, "address":0xF030, "scale":1/10, "bias":0, "round":1, "param":0x00000000}, #s
            "set_Current_Alarm_Low_Limit":      {"fcr":0x03, "fcw":0x10, "address":0xF031, "scale":1/10, "bias":0, "round":1, "param":0x00000000},#% Always set below the Up limit address: F02D

            "set_Voltage_Alarm_Upp_Limit":      {"fcr":0x03, "fcw":0x10, "address":0xF032, "scale":1/10, "bias":0, "round":1, "param":0x0000044C}, #%
            "set_Voltage_Alarm_Hysteresis":     {"fcr":0x03, "fcw":0x10, "address":0xF033, "scale":1/10, "bias":0, "round":1, "param":0x00000032}, #%
            "set_Voltage_Alarm_OFF_Delay":      {"fcr":0x03, "fcw":0x10, "address":0xF034, "scale":1/10, "bias":0, "round":1, "param":0x0000001E}, #s
            "set_Voltage_Alarm_ON_Delay":       {"fcr":0x03, "fcw":0x10, "address":0xF035, "scale":1/10, "bias":0, "round":1, "param":0x00000000}, #s
            "set_Voltage_Alarm_Low_Limit":      {"fcr":0x03, "fcw":0x10, "address":0xF036, "scale":1/10, "bias":0, "round":1, "param":0x00000000},#% Always set below the Up limit address: F032

            "set_PF_Alarm_Upp_Limit":           {"fcr":0x03, "fcw":0x10, "address":0xF037, "scale":1/10, "bias":0, "round":1, "param":0x000003E8}, #%
            "set_PF_Alarm_Hysteresis":          {"fcr":0x03, "fcw":0x10, "address":0xF038, "scale":1/10, "bias":0, "round":1, "param":0x00000032}, #%
            "set_PF_Alarm_OFF_Delay":           {"fcr":0x03, "fcw":0x10, "address":0xF039, "scale":1/10, "bias":0, "round":1, "param":0x0000001E}, #s
            "set_PF_Alarm_ON_Delay":            {"fcr":0x03, "fcw":0x10, "address":0xF03A, "scale":1/10, "bias":0, "round":1, "param":0x00000000}, #s
            "set_PF_Alarm_Low_Limit":           {"fcr":0x03, "fcw":0x10, "address":0xF03B, "scale":1/10, "bias":0, "round":1, "param":0x00000000},#% Always set below the Up limit address: F037

            "set_React_Power_Alarm_Upp_Limit":  {"fcr":0x03, "fcw":0x10, "address":0xF03C, "scale":1/10, "bias":0, "round":1, "param":0x00000320}, #%
            "set_React_Power_Alarm_Hysteresis": {"fcr":0x03, "fcw":0x10, "address":0xF03D, "scale":1/10, "bias":0, "round":1, "param":0x00000032}, #%
            "set_React_Power_Alarm_OFF_Delay":  {"fcr":0x03, "fcw":0x10, "address":0xF03E, "scale":1/10, "bias":0, "round":1, "param":0x0000001E}, #s
            "set_React_Power_Alarm_ON_Delay":   {"fcr":0x03, "fcw":0x10, "address":0xF03F, "scale":1/10, "bias":0, "round":1, "param":0x00000000}, #s
            "set_React_Power_Alarm_Low_Limit":  {"fcr":0x03, "fcw":0x10, "address":0xF040, "scale":1/10, "bias":0, "round":1, "param":0x00000000},# Always set below the Up limit address: F03C
            
            "set_Output_Terminal_1_Function":   {"fcr":0x03, "fcw":0x10, "address":0xF041, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Active_Power_Alarm_OT1":       {"fcr":0x03, "fcw":0x10, "address":0xF043, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Regene_Power_Alarm_OT1":       {"fcr":0x03, "fcw":0x10, "address":0xF044, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Current_Alarm_OT1":            {"fcr":0x03, "fcw":0x10, "address":0xF045, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Voltage_Alarm_OT1":            {"fcr":0x03, "fcw":0x10, "address":0xF046, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_PF_Alarm_OT1":                 {"fcr":0x03, "fcw":0x10, "address":0xF047, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_React_Power_Alarm_OT1":        {"fcr":0x03, "fcw":0x10, "address":0xF048, "scale":1, "bias":0, "round":0, "param":0x00000000},

            #"set_Output_Terminal_2_Function":   {"fcr":0x03, "fcw":0x10, "address":0xF042, "scale":1, "bias":0, "round":0, "param":0x00000001}, # KM50-E Only
            #"set_Active_Power_Alarm_OT2":       {"fcr":0x03, "fcw":0x10, "address":0xF049, "scale":1, "bias":0, "round":0, "param":0x00000000}, # KM50-E Only
            #"set_Regene_Power_Alarm_OT2":       {"fcr":0x03, "fcw":0x10, "address":0xF04A, "scale":1, "bias":0, "round":0, "param":0x00000000}, # KM50-E Only
            #"set_Current_Alarm_OT2":            {"fcr":0x03, "fcw":0x10, "address":0xF04B, "scale":1, "bias":0, "round":0, "param":0x00000000}, # KM50-E Only
            #"set_Voltage_Alarm_OT2":            {"fcr":0x03, "fcw":0x10, "address":0xF04C, "scale":1, "bias":0, "round":0, "param":0x00000000}, # KM50-E Only
            #"set_PF_Alarm_OT2":                 {"fcr":0x03, "fcw":0x10, "address":0xF04D, "scale":1, "bias":0, "round":0, "param":0x00000000}, # KM50-E Only
            #"set_React_Power_Alarm_OT2":        {"fcr":0x03, "fcw":0x10, "address":0xF04E, "scale":1, "bias":0, "round":0, "param":0x00000000}, # KM50-E Only

            "set_Auto_Rotate_Function":         {"fcr":0x03, "fcw":0x10, "address":0xF04F, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Transition_Time":              {"fcr":0x03, "fcw":0x10, "address":0xF050, "scale":1, "bias":0, "round":0, "param":0x00000003}, #s
            "set_Active_Power_Display_Select":  {"fcr":0x03, "fcw":0x10, "address":0xF051, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Total_Power_Display_Select":   {"fcr":0x03, "fcw":0x10, "address":0xF052, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Current_1_Display_Select":     {"fcr":0x03, "fcw":0x10, "address":0xF053, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Current_2_Display_Select":     {"fcr":0x03, "fcw":0x10, "address":0xF054, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Current_3_Display_Select":     {"fcr":0x03, "fcw":0x10, "address":0xF055, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Voltage_1_Display_Select":     {"fcr":0x03, "fcw":0x10, "address":0xF056, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Voltage_2_Display_Select":     {"fcr":0x03, "fcw":0x10, "address":0xF057, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Voltage_3_Display_Select":     {"fcr":0x03, "fcw":0x10, "address":0xF058, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_PF_Display_Select":            {"fcr":0x03, "fcw":0x10, "address":0xF059, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_React_Power_Display_Select":   {"fcr":0x03, "fcw":0x10, "address":0xF05A, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Frequency_Display_Select":     {"fcr":0x03, "fcw":0x10, "address":0xF05B, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_CO2_Display_Select":           {"fcr":0x03, "fcw":0x10, "address":0xF05C, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Conv_Mone_Cost_Display_Select":{"fcr":0x03, "fcw":0x10, "address":0xF05D, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_GP_Pulse_Conv1_Display_Select":{"fcr":0x03, "fcw":0x10, "address":0xF05E, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_GP_Pulse_Conv2_Display_Select":{"fcr":0x03, "fcw":0x10, "address":0xF05F, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Time_Display_Select":          {"fcr":0x03, "fcw":0x10, "address":0xF060, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Cons_Spe_Power_Display_Select":{"fcr":0x03, "fcw":0x10, "address":0xF062, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Regene_Total_Display_Select":  {"fcr":0x03, "fcw":0x10, "address":0xF06A, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Lead_React_Display_Select":    {"fcr":0x03, "fcw":0x10, "address":0xF06B, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Lagg_React_Display_Select":    {"fcr":0x03, "fcw":0x10, "address":0xF06C, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_React_Total_Display_Select":   {"fcr":0x03, "fcw":0x10, "address":0xF06D, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Temperature_Display_Select":   {"fcr":0x03, "fcw":0x10, "address":0xF06E, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Product_Information":          {"fcr":0x03, "fcw":0x10, "address":0xF06F, "scale":1, "bias":0, "round":0, "param":0x00000001},

            "set_Temperature_Unit":             {"fcr":0x03, "fcw":0x10, "address":0xF073, "scale":1, "bias":0, "round":0, "param":0x00000000}, #C or F
            "set_Temperature_Compensation":     {"fcr":0x03, "fcw":0x10, "address":0xF074, "scale":1/10, "bias":0, "round":1, "param":0x00000000},
            "set_Display_ON_Time":              {"fcr":0x03, "fcw":0x10, "address":0xF075, "scale":1, "bias":0, "round":0, "param":0x00000000}, # minutes
            "set_Incorrect_Writing_Detection":  {"fcr":0x03, "fcw":0x10, "address":0xF076, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Conv_Mone_Cost_Rate":          {"fcr":0x03, "fcw":0x10, "address":0xF077, "scale":1, "bias":0, "round":0, "param":0x00002710},
            "set_Currency":                     {"fcr":0x03, "fcw":0x10, "address":0xF078, "scale":1, "bias":0, "round":0, "param":0x204A5059}, # Check manual for setting page 5-45
            "set_Pulse_Conv_1_Target":          {"fcr":0x03, "fcw":0x10, "address":0xF079, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Pulse_Conv_2_Target":          {"fcr":0x03, "fcw":0x10, "address":0xF07A, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Coefficient_1":                {"fcr":0x03, "fcw":0x10, "address":0xF07B, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Coefficient_2":                {"fcr":0x03, "fcw":0x10, "address":0xF07C, "scale":1, "bias":0, "round":0, "param":0x00000001},
            "set_Dec_Point_Position_1":         {"fcr":0x03, "fcw":0x10, "address":0xF07D, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Dec_Point_Position_2":         {"fcr":0x03, "fcw":0x10, "address":0xF07E, "scale":1, "bias":0, "round":0, "param":0x00000000},
            "set_Display_Unit_1":               {"fcr":0x03, "fcw":0x10, "address":0xF07F, "scale":1, "bias":0, "round":0, "param":0x4D332F31}, # Check manual for setting page 5-46
            "set_Display_Unit_2":               {"fcr":0x03, "fcw":0x10, "address":0xF080, "scale":1, "bias":0, "round":0, "param":0x4D332F31}, # Check manual for setting page 5-46
            "set_Voltage_VT_Secondary":         {"fcr":0x03, "fcw":0x10, "address":0xF081, "scale":1, "bias":0, "round":0, "param":0x00000000}, #V

            "set_Time_Data_YYMMDD":             {"fcr":0x03, "fcw":0x10, "address":0xFF00, "scale":1, "bias":0, "round":0, "param":0x00000000}, #00YY MMDD; 00 00~63 00~0C 00~1F
            "set_Time_Data_HHMM":               {"fcr":0x03, "fcw":0x10, "address":0xFF01, "scale":1, "bias":0, "round":0, "param":0x00000000}, #0000 HHmm; 00  00   00~17 00~3B
            "Controller_Attr_1":                {"fcr":0x03, "fcw":None, "address":0xFF02, "scale":1, "bias":0, "round":0},
            "Controller_Attr_2":                {"fcr":0x03, "fcw":None, "address":0xFF03, "scale":1, "bias":0, "round":0},
            "Controller_Attr_3":                {"fcr":0x03, "fcw":None, "address":0xFF04, "scale":1, "bias":0, "round":0},
            "Controller_Attr_4":                {"fcr":0x03, "fcw":None, "address":0xFF05, "scale":1, "bias":0, "round":0},
            "Controller_Status":                {"fcr":0x03, "fcw":None, "address":0xFF06, "scale":1, "bias":0, "round":0}
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
