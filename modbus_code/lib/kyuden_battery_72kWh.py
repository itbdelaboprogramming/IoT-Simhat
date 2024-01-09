"""
#title           :kyuden_battery_72kWh.py
#description     :modbus library for Kyuden Battery (BMS) 72kWh
#author          :Nicholas Putra Rihandoko, Nauval Chantika
#date            :2023/10/15
#version         :1.0
#usage           :Energy Monitoring System
#notes           :
#python_version  :3.11.2
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
            ## Read Status (bit Type) (Don't have "scale", "bias", and "round")
            "Operation_State":          {"fcr":0x02, "fcw":None, "address":0x0000, "scale":1, "bias":0, "round":0},
            "Initialization_State":     {"fcr":0x02, "fcw":None, "address":0x0001, "scale":1, "bias":0, "round":0},
            "Standby_State":            {"fcr":0x02, "fcw":None, "address":0x0002, "scale":1, "bias":0, "round":0},
            "Output_State":             {"fcr":0x02, "fcw":None, "address":0x0003, "scale":1, "bias":0, "round":0},
            "Electrification_State":    {"fcr":0x02, "fcw":None, "address":0x0004, "scale":1, "bias":0, "round":0},
            "Error_State":              {"fcr":0x02, "fcw":None, "address":0x0005, "scale":1, "bias":0, "round":0},
            "Shutdown_State":           {"fcr":0x02, "fcw":None, "address":0x0006, "scale":1, "bias":0, "round":0},
            "BMS_Contactor_State":      {"fcr":0x02, "fcw":None, "address":0x0007, "scale":1, "bias":0, "round":0},
            "Output_Contactor_State":   {"fcr":0x02, "fcw":None, "address":0x0008, "scale":1, "bias":0, "round":0},
            "Cell_Balance_State":       {"fcr":0x02, "fcw":None, "address":0x0009, "scale":1, "bias":0, "round":0},
            "Alert_State":              {"fcr":0x02, "fcw":None, "address":0x000A, "scale":1, "bias":0, "round":0},
            ## Read Input Register (str Type) (Several Doesn't Have "scale", "bias", and "round")
            "Firmware_Version":         {"fcr":0x04, "fcw":None, "address":0x1000, "scale":1, "bias":0, "round":0},
            "Count_Module":             {"fcr":0x04, "fcw":None, "address":0x1003, "scale":1, "bias":0, "round":0},
            "Count_Module_Series":      {"fcr":0x04, "fcw":None, "address":0x1004, "scale":1, "bias":0, "round":0},
            "Count_Module_Parallel":    {"fcr":0x04, "fcw":None, "address":0x1005, "scale":1, "bias":0, "round":0},
            "Count_CMU":                {"fcr":0x04, "fcw":None, "address":0x1006, "scale":1, "bias":0, "round":0},
            
            "Status":                   {"fcr":0x04, "fcw":None, "address":0x1010, "scale":1, "bias":0, "round":0},
            "Error":                    {"fcr":0x04, "fcw":None, "address":0x1011, "scale":1, "bias":0, "round":0},
            "SOC":                      {"fcr":0x04, "fcw":None, "address":0x1012, "scale":1, "bias":0, "round":0},
            "Total_Voltage":            {"fcr":0x04, "fcw":None, "address":0x1013, "scale":1/10, "bias":0, "round":1},
            "Cell_Voltage_max":         {"fcr":0x04, "fcw":None, "address":0x1014, "scale":1/1000, "bias":0, "round":2},
            "Cell_Voltage_min":         {"fcr":0x04, "fcw":None, "address":0x1015, "scale":1/1000, "bias":0, "round":2},
            "Cell_Voltage_avg":         {"fcr":0x04, "fcw":None, "address":0x1016, "scale":1/1000, "bias":0, "round":2},
            "Temperature_max":          {"fcr":0x04, "fcw":None, "address":0x1017, "scale":1, "bias":-55, "round":0},
            "Temperature_min":          {"fcr":0x04, "fcw":None, "address":0x1018, "scale":1, "bias":-55, "round":0},
            "Temperature_avg":          {"fcr":0x04, "fcw":None, "address":0x1019, "scale":1, "bias":-55, "round":0},
            "Balance_Voltage":          {"fcr":0x04, "fcw":None, "address":0x101A, "scale":1/1000, "bias":0, "round":2},
            "Balance_Voltage_diff":     {"fcr":0x04, "fcw":None, "address":0x101B, "scale":1/1000, "bias":0, "round":2},
            "Mode":                     {"fcr":0x04, "fcw":None, "address":0x101C, "scale":1, "bias":0, "round":0},

            "Voltage_M1":               {"fcr":0x04, "fcw":None, "address":0x1100, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C1":            {"fcr":0x04, "fcw":None, "address":0x1101, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C2":            {"fcr":0x04, "fcw":None, "address":0x1102, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C3":            {"fcr":0x04, "fcw":None, "address":0x1103, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C4":            {"fcr":0x04, "fcw":None, "address":0x1104, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C5":            {"fcr":0x04, "fcw":None, "address":0x1105, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C6":            {"fcr":0x04, "fcw":None, "address":0x1106, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C7":            {"fcr":0x04, "fcw":None, "address":0x1107, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C8":            {"fcr":0x04, "fcw":None, "address":0x1108, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C9":            {"fcr":0x04, "fcw":None, "address":0x1109, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C10":           {"fcr":0x04, "fcw":None, "address":0x110A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C11":           {"fcr":0x04, "fcw":None, "address":0x110B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M1_C12":           {"fcr":0x04, "fcw":None, "address":0x110C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M1_1":         {"fcr":0x04, "fcw":None, "address":0x110D, "scale":1, "bias":55, "round":0},
            "Temperature_M1_2":         {"fcr":0x04, "fcw":None, "address":0x110E, "scale":1, "bias":55, "round":0},

            "Voltage_M2":               {"fcr":0x04, "fcw":None, "address":0x1110, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C1":            {"fcr":0x04, "fcw":None, "address":0x1111, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C2":            {"fcr":0x04, "fcw":None, "address":0x1112, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C3":            {"fcr":0x04, "fcw":None, "address":0x1113, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C4":            {"fcr":0x04, "fcw":None, "address":0x1114, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C5":            {"fcr":0x04, "fcw":None, "address":0x1115, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C6":            {"fcr":0x04, "fcw":None, "address":0x1116, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C7":            {"fcr":0x04, "fcw":None, "address":0x1117, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C8":            {"fcr":0x04, "fcw":None, "address":0x1118, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C9":            {"fcr":0x04, "fcw":None, "address":0x1119, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C10":           {"fcr":0x04, "fcw":None, "address":0x111A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C11":           {"fcr":0x04, "fcw":None, "address":0x111B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M2_C12":           {"fcr":0x04, "fcw":None, "address":0x111C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M2_1":         {"fcr":0x04, "fcw":None, "address":0x111D, "scale":1, "bias":55, "round":0},
            "Temperature_M2_2":         {"fcr":0x04, "fcw":None, "address":0x111E, "scale":1, "bias":55, "round":0},

            "Voltage_M3":               {"fcr":0x04, "fcw":None, "address":0x1120, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C1":            {"fcr":0x04, "fcw":None, "address":0x1121, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C2":            {"fcr":0x04, "fcw":None, "address":0x1122, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C3":            {"fcr":0x04, "fcw":None, "address":0x1123, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C4":            {"fcr":0x04, "fcw":None, "address":0x1124, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C5":            {"fcr":0x04, "fcw":None, "address":0x1125, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C6":            {"fcr":0x04, "fcw":None, "address":0x1126, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C7":            {"fcr":0x04, "fcw":None, "address":0x1127, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C8":            {"fcr":0x04, "fcw":None, "address":0x1128, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C9":            {"fcr":0x04, "fcw":None, "address":0x1129, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C10":           {"fcr":0x04, "fcw":None, "address":0x112A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C11":           {"fcr":0x04, "fcw":None, "address":0x112B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M3_C12":           {"fcr":0x04, "fcw":None, "address":0x112C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M3_1":         {"fcr":0x04, "fcw":None, "address":0x112D, "scale":1, "bias":55, "round":0},
            "Temperature_M3_2":         {"fcr":0x04, "fcw":None, "address":0x112E, "scale":1, "bias":55, "round":0},

            "Voltage_M4":               {"fcr":0x04, "fcw":None, "address":0x1130, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C1":            {"fcr":0x04, "fcw":None, "address":0x1131, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C2":            {"fcr":0x04, "fcw":None, "address":0x1132, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C3":            {"fcr":0x04, "fcw":None, "address":0x1133, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C4":            {"fcr":0x04, "fcw":None, "address":0x1134, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C5":            {"fcr":0x04, "fcw":None, "address":0x1135, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C6":            {"fcr":0x04, "fcw":None, "address":0x1136, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C7":            {"fcr":0x04, "fcw":None, "address":0x1137, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C8":            {"fcr":0x04, "fcw":None, "address":0x1138, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C9":            {"fcr":0x04, "fcw":None, "address":0x1139, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C10":           {"fcr":0x04, "fcw":None, "address":0x113A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C11":           {"fcr":0x04, "fcw":None, "address":0x113B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M4_C12":           {"fcr":0x04, "fcw":None, "address":0x113C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M4_1":         {"fcr":0x04, "fcw":None, "address":0x113D, "scale":1, "bias":55, "round":0},
            "Temperature_M4_2":         {"fcr":0x04, "fcw":None, "address":0x113E, "scale":1, "bias":55, "round":0},

            "Voltage_M5":               {"fcr":0x04, "fcw":None, "address":0x1140, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C1":            {"fcr":0x04, "fcw":None, "address":0x1141, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C2":            {"fcr":0x04, "fcw":None, "address":0x1142, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C3":            {"fcr":0x04, "fcw":None, "address":0x1143, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C4":            {"fcr":0x04, "fcw":None, "address":0x1144, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C5":            {"fcr":0x04, "fcw":None, "address":0x1145, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C6":            {"fcr":0x04, "fcw":None, "address":0x1146, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C7":            {"fcr":0x04, "fcw":None, "address":0x1147, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C8":            {"fcr":0x04, "fcw":None, "address":0x1148, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C9":            {"fcr":0x04, "fcw":None, "address":0x1149, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C10":           {"fcr":0x04, "fcw":None, "address":0x114A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C11":           {"fcr":0x04, "fcw":None, "address":0x114B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M5_C12":           {"fcr":0x04, "fcw":None, "address":0x114C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M5_1":         {"fcr":0x04, "fcw":None, "address":0x114D, "scale":1, "bias":55, "round":0},
            "Temperature_M5_2":         {"fcr":0x04, "fcw":None, "address":0x114E, "scale":1, "bias":55, "round":0},

            "Voltage_M6":               {"fcr":0x04, "fcw":None, "address":0x1150, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C1":            {"fcr":0x04, "fcw":None, "address":0x1151, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C2":            {"fcr":0x04, "fcw":None, "address":0x1152, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C3":            {"fcr":0x04, "fcw":None, "address":0x1153, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C4":            {"fcr":0x04, "fcw":None, "address":0x1154, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C5":            {"fcr":0x04, "fcw":None, "address":0x1155, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C6":            {"fcr":0x04, "fcw":None, "address":0x1156, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C7":            {"fcr":0x04, "fcw":None, "address":0x1157, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C8":            {"fcr":0x04, "fcw":None, "address":0x1158, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C9":            {"fcr":0x04, "fcw":None, "address":0x1159, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C10":           {"fcr":0x04, "fcw":None, "address":0x115A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C11":           {"fcr":0x04, "fcw":None, "address":0x115B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M6_C12":           {"fcr":0x04, "fcw":None, "address":0x115C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M6_1":         {"fcr":0x04, "fcw":None, "address":0x115D, "scale":1, "bias":55, "round":0},
            "Temperature_M6_2":         {"fcr":0x04, "fcw":None, "address":0x115E, "scale":1, "bias":55, "round":0},

            "Voltage_M7":               {"fcr":0x04, "fcw":None, "address":0x1160, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C1":            {"fcr":0x04, "fcw":None, "address":0x1161, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C2":            {"fcr":0x04, "fcw":None, "address":0x1162, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C3":            {"fcr":0x04, "fcw":None, "address":0x1163, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C4":            {"fcr":0x04, "fcw":None, "address":0x1164, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C5":            {"fcr":0x04, "fcw":None, "address":0x1165, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C6":            {"fcr":0x04, "fcw":None, "address":0x1166, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C7":            {"fcr":0x04, "fcw":None, "address":0x1167, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C8":            {"fcr":0x04, "fcw":None, "address":0x1168, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C9":            {"fcr":0x04, "fcw":None, "address":0x1169, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C10":           {"fcr":0x04, "fcw":None, "address":0x116A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C11":           {"fcr":0x04, "fcw":None, "address":0x116B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M7_C12":           {"fcr":0x04, "fcw":None, "address":0x116C, "scale":1/1000, "bias":0, "round":2},
            "Temperatute_M7_1":         {"fcr":0x04, "fcw":None, "address":0x116D, "scale":1, "bias":55, "round":0},
            "Temperature_M7_2":         {"fcr":0x04, "fcw":None, "address":0x116E, "scale":1, "bias":55, "round":0},

            "Voltage_M8":               {"fcr":0x04, "fcw":None, "address":0x1170, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C1":            {"fcr":0x04, "fcw":None, "address":0x1171, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C2":            {"fcr":0x04, "fcw":None, "address":0x1172, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C3":            {"fcr":0x04, "fcw":None, "address":0x1173, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C4":            {"fcr":0x04, "fcw":None, "address":0x1174, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C5":            {"fcr":0x04, "fcw":None, "address":0x1175, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C6":            {"fcr":0x04, "fcw":None, "address":0x1176, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C7":            {"fcr":0x04, "fcw":None, "address":0x1177, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C8":            {"fcr":0x04, "fcw":None, "address":0x1178, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C9":            {"fcr":0x04, "fcw":None, "address":0x1179, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C10":           {"fcr":0x04, "fcw":None, "address":0x117A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C11":           {"fcr":0x04, "fcw":None, "address":0x117B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M8_C12":           {"fcr":0x04, "fcw":None, "address":0x117C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M8_1":         {"fcr":0x04, "fcw":None, "address":0x117D, "scale":1, "bias":55, "round":0},
            "Temperature_M8_2":         {"fcr":0x04, "fcw":None, "address":0x117E, "scale":1, "bias":55, "round":0},

            "Voltage_M9":               {"fcr":0x04, "fcw":None, "address":0x1180, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C1":            {"fcr":0x04, "fcw":None, "address":0x1181, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C2":            {"fcr":0x04, "fcw":None, "address":0x1182, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C3":            {"fcr":0x04, "fcw":None, "address":0x1183, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C4":            {"fcr":0x04, "fcw":None, "address":0x1184, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C5":            {"fcr":0x04, "fcw":None, "address":0x1185, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C6":            {"fcr":0x04, "fcw":None, "address":0x1186, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C7":            {"fcr":0x04, "fcw":None, "address":0x1187, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C8":            {"fcr":0x04, "fcw":None, "address":0x1188, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C9":            {"fcr":0x04, "fcw":None, "address":0x1189, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C10":           {"fcr":0x04, "fcw":None, "address":0x118A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C11":           {"fcr":0x04, "fcw":None, "address":0x118B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M9_C12":           {"fcr":0x04, "fcw":None, "address":0x118C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M9_1":         {"fcr":0x04, "fcw":None, "address":0x118D, "scale":1, "bias":55, "round":0},
            "Temperature_M9_2":         {"fcr":0x04, "fcw":None, "address":0x118E, "scale":1, "bias":55, "round":0},

            "Voltage_M10":              {"fcr":0x04, "fcw":None, "address":0x1190, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C1":           {"fcr":0x04, "fcw":None, "address":0x1191, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C2":           {"fcr":0x04, "fcw":None, "address":0x1192, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C3":           {"fcr":0x04, "fcw":None, "address":0x1193, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C4":           {"fcr":0x04, "fcw":None, "address":0x1194, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C5":           {"fcr":0x04, "fcw":None, "address":0x1195, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C6":           {"fcr":0x04, "fcw":None, "address":0x1196, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C7":           {"fcr":0x04, "fcw":None, "address":0x1197, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C8":           {"fcr":0x04, "fcw":None, "address":0x1198, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C9":           {"fcr":0x04, "fcw":None, "address":0x1199, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C10":          {"fcr":0x04, "fcw":None, "address":0x119A, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C11":          {"fcr":0x04, "fcw":None, "address":0x119B, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M10_C12":          {"fcr":0x04, "fcw":None, "address":0x119C, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M10_1":        {"fcr":0x04, "fcw":None, "address":0x119D, "scale":1, "bias":55, "round":0},
            "Temperature_M10_2":        {"fcr":0x04, "fcw":None, "address":0x119E, "scale":1, "bias":55, "round":0},

            "Voltage_M11":              {"fcr":0x04, "fcw":None, "address":0x11A0, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C1":           {"fcr":0x04, "fcw":None, "address":0x11A1, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C2":           {"fcr":0x04, "fcw":None, "address":0x11A2, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C3":           {"fcr":0x04, "fcw":None, "address":0x11A3, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C4":           {"fcr":0x04, "fcw":None, "address":0x11A4, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C5":           {"fcr":0x04, "fcw":None, "address":0x11A5, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C6":           {"fcr":0x04, "fcw":None, "address":0x11A6, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C7":           {"fcr":0x04, "fcw":None, "address":0x11A7, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C8":           {"fcr":0x04, "fcw":None, "address":0x11A8, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C9":           {"fcr":0x04, "fcw":None, "address":0x11A9, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C10":          {"fcr":0x04, "fcw":None, "address":0x11AA, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C11":          {"fcr":0x04, "fcw":None, "address":0x11AB, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M11_C12":          {"fcr":0x04, "fcw":None, "address":0x11AC, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M11_1":        {"fcr":0x04, "fcw":None, "address":0x11AD, "scale":1, "bias":55, "round":0},
            "Temperature_M11_2":        {"fcr":0x04, "fcw":None, "address":0x11AE, "scale":1, "bias":55, "round":0},

            "Voltage_M12":              {"fcr":0x04, "fcw":None, "address":0x11B0, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C1":           {"fcr":0x04, "fcw":None, "address":0x11B1, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C2":           {"fcr":0x04, "fcw":None, "address":0x11B2, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C3":           {"fcr":0x04, "fcw":None, "address":0x11B3, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C4":           {"fcr":0x04, "fcw":None, "address":0x11B4, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C5":           {"fcr":0x04, "fcw":None, "address":0x11B5, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C6":           {"fcr":0x04, "fcw":None, "address":0x11B6, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C7":           {"fcr":0x04, "fcw":None, "address":0x11B7, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C8":           {"fcr":0x04, "fcw":None, "address":0x11B8, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C9":           {"fcr":0x04, "fcw":None, "address":0x11B9, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C10":          {"fcr":0x04, "fcw":None, "address":0x11BA, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C11":          {"fcr":0x04, "fcw":None, "address":0x11BB, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M12_C12":          {"fcr":0x04, "fcw":None, "address":0x11BC, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M12_1":        {"fcr":0x04, "fcw":None, "address":0x11BD, "scale":1, "bias":55, "round":0},
            "Temperature_M12_2":        {"fcr":0x04, "fcw":None, "address":0x11BE, "scale":1, "bias":55, "round":0},

            "Voltage_M13":              {"fcr":0x04, "fcw":None, "address":0x11C0, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C1":           {"fcr":0x04, "fcw":None, "address":0x11C1, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C2":           {"fcr":0x04, "fcw":None, "address":0x11C2, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C3":           {"fcr":0x04, "fcw":None, "address":0x11C3, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C4":           {"fcr":0x04, "fcw":None, "address":0x11C4, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C5":           {"fcr":0x04, "fcw":None, "address":0x11C5, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C6":           {"fcr":0x04, "fcw":None, "address":0x11C6, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C7":           {"fcr":0x04, "fcw":None, "address":0x11C7, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C8":           {"fcr":0x04, "fcw":None, "address":0x11C8, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C9":           {"fcr":0x04, "fcw":None, "address":0x11C9, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C10":          {"fcr":0x04, "fcw":None, "address":0x11CA, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C11":          {"fcr":0x04, "fcw":None, "address":0x11CB, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M13_C12":          {"fcr":0x04, "fcw":None, "address":0x11CC, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M13_1":        {"fcr":0x04, "fcw":None, "address":0x11CD, "scale":1, "bias":55, "round":0},
            "Temperature_M13_2":        {"fcr":0x04, "fcw":None, "address":0x11CE, "scale":1, "bias":55, "round":0},
        
            "Voltage_M14":              {"fcr":0x04, "fcw":None, "address":0x11D0, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C1":           {"fcr":0x04, "fcw":None, "address":0x11D1, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C2":           {"fcr":0x04, "fcw":None, "address":0x11D2, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C3":           {"fcr":0x04, "fcw":None, "address":0x11D3, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C4":           {"fcr":0x04, "fcw":None, "address":0x11D4, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C5":           {"fcr":0x04, "fcw":None, "address":0x11D5, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C6":           {"fcr":0x04, "fcw":None, "address":0x11D6, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C7":           {"fcr":0x04, "fcw":None, "address":0x11D7, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C8":           {"fcr":0x04, "fcw":None, "address":0x11D8, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C9":           {"fcr":0x04, "fcw":None, "address":0x11D9, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C10":          {"fcr":0x04, "fcw":None, "address":0x11DA, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C11":          {"fcr":0x04, "fcw":None, "address":0x11DB, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M14_C12":          {"fcr":0x04, "fcw":None, "address":0x11DC, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M14_1":        {"fcr":0x04, "fcw":None, "address":0x11DD, "scale":1, "bias":55, "round":0},
            "Temperature_M14_2":        {"fcr":0x04, "fcw":None, "address":0x11DE, "scale":1, "bias":55, "round":0},

            "Voltage_M15":              {"fcr":0x04, "fcw":None, "address":0x11E0, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C1":           {"fcr":0x04, "fcw":None, "address":0x11E1, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C2":           {"fcr":0x04, "fcw":None, "address":0x11E2, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C3":           {"fcr":0x04, "fcw":None, "address":0x11E3, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C4":           {"fcr":0x04, "fcw":None, "address":0x11E4, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C5":           {"fcr":0x04, "fcw":None, "address":0x11E5, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C6":           {"fcr":0x04, "fcw":None, "address":0x11E6, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C7":           {"fcr":0x04, "fcw":None, "address":0x11E7, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C8":           {"fcr":0x04, "fcw":None, "address":0x11E8, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C9":           {"fcr":0x04, "fcw":None, "address":0x11E9, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C10":          {"fcr":0x04, "fcw":None, "address":0x11EA, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C11":          {"fcr":0x04, "fcw":None, "address":0x11EB, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M15_C12":          {"fcr":0x04, "fcw":None, "address":0x11EC, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M15_1":        {"fcr":0x04, "fcw":None, "address":0x11ED, "scale":1, "bias":55, "round":0},
            "Temperature_M15_2":        {"fcr":0x04, "fcw":None, "address":0x11EE, "scale":1, "bias":55, "round":0},

            "Voltage_M16":              {"fcr":0x04, "fcw":None, "address":0x11F0, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C1":           {"fcr":0x04, "fcw":None, "address":0x11F1, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C2":           {"fcr":0x04, "fcw":None, "address":0x11F2, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C3":           {"fcr":0x04, "fcw":None, "address":0x11F3, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C4":           {"fcr":0x04, "fcw":None, "address":0x11F4, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C5":           {"fcr":0x04, "fcw":None, "address":0x11F5, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C6":           {"fcr":0x04, "fcw":None, "address":0x11F6, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C7":           {"fcr":0x04, "fcw":None, "address":0x11F7, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C8":           {"fcr":0x04, "fcw":None, "address":0x11F8, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C9":           {"fcr":0x04, "fcw":None, "address":0x11F9, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C10":          {"fcr":0x04, "fcw":None, "address":0x11FA, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C11":          {"fcr":0x04, "fcw":None, "address":0x11FB, "scale":1/1000, "bias":0, "round":2},
            "Voltage_M16_C12":          {"fcr":0x04, "fcw":None, "address":0x11FC, "scale":1/1000, "bias":0, "round":2},
            "Temperature_M16_1":        {"fcr":0x04, "fcw":None, "address":0x11FD, "scale":1, "bias":55, "round":0},
            "Temperature_M16_2":        {"fcr":0x04, "fcw":None, "address":0x11FE, "scale":1, "bias":55, "round":0},

            "Temperature_M1_3":         {"fcr":0x04, "fcw":None, "address":0x1200, "scale":1, "bias":55, "round":0},
            "Temperature_M2_3":         {"fcr":0x04, "fcw":None, "address":0x1201, "scale":1, "bias":55, "round":0},
            "Temperature_M3_3":         {"fcr":0x04, "fcw":None, "address":0x1202, "scale":1, "bias":55, "round":0},
            "Temperature_M4_3":         {"fcr":0x04, "fcw":None, "address":0x1203, "scale":1, "bias":55, "round":0},
            "Temperature_M5_3":         {"fcr":0x04, "fcw":None, "address":0x1204, "scale":1, "bias":55, "round":0},
            "Temperature_M6_3":         {"fcr":0x04, "fcw":None, "address":0x1205, "scale":1, "bias":55, "round":0},
            "Temperature_M7_3":         {"fcr":0x04, "fcw":None, "address":0x1206, "scale":1, "bias":55, "round":0},
            "Temperature_M8_3":         {"fcr":0x04, "fcw":None, "address":0x1207, "scale":1, "bias":55, "round":0},
            "Temperature_M9_3":         {"fcr":0x04, "fcw":None, "address":0x1208, "scale":1, "bias":55, "round":0},
            "Temperature_M10_3":        {"fcr":0x04, "fcw":None, "address":0x1209, "scale":1, "bias":55, "round":0},
            "Temperature_M11_3":        {"fcr":0x04, "fcw":None, "address":0x120A, "scale":1, "bias":55, "round":0},
            "Temperature_M12_3":        {"fcr":0x04, "fcw":None, "address":0x120B, "scale":1, "bias":55, "round":0},
            "Temperature_M13_3":        {"fcr":0x04, "fcw":None, "address":0x120C, "scale":1, "bias":55, "round":0},
            "Temperature_M14_3":        {"fcr":0x04, "fcw":None, "address":0x120D, "scale":1, "bias":55, "round":0},
            "Temperature_M15_3":        {"fcr":0x04, "fcw":None, "address":0x120E, "scale":1, "bias":55, "round":0},
            "Temperature_M16_3":        {"fcr":0x04, "fcw":None, "address":0x120F, "scale":1, "bias":55, "round":0},

            "Last_Error":               {"fcr":0x04, "fcw":None, "address":0x1020, "scale":1, "bias":0, "round":0},
            "Prev_Error_1":             {"fcr":0x04, "fcw":None, "address":0x1021, "scale":1, "bias":0, "round":0},
            "Prev_Error_2":             {"fcr":0x04, "fcw":None, "address":0x1022, "scale":1, "bias":0, "round":0},
            "Prev_Error_3":             {"fcr":0x04, "fcw":None, "address":0x1023, "scale":1, "bias":0, "round":0},
            "Prev_Error_4":             {"fcr":0x04, "fcw":None, "address":0x1024, "scale":1, "bias":0, "round":0},
            "Prev_Error_5":             {"fcr":0x04, "fcw":None, "address":0x1025, "scale":1, "bias":0, "round":0},
                # Size is 2 Bytes and each bit is represent each cell in a module (1-12); 0 or 1; 123456789ABC0000
            "CBAL_M1":                  {"fcr":0x04, "fcw":None, "address":0x110F, "scale":1, "bias":0, "round":0},
            "CBAL_M2":                  {"fcr":0x04, "fcw":None, "address":0x111F, "scale":1, "bias":0, "round":0},
            "CBAL_M3":                  {"fcr":0x04, "fcw":None, "address":0x112F, "scale":1, "bias":0, "round":0},
            "CBAL_M4":                  {"fcr":0x04, "fcw":None, "address":0x113F, "scale":1, "bias":0, "round":0},
            "CBAL_M5":                  {"fcr":0x04, "fcw":None, "address":0x114F, "scale":1, "bias":0, "round":0},
            "CBAL_M6":                  {"fcr":0x04, "fcw":None, "address":0x115F, "scale":1, "bias":0, "round":0},
            "CBAL_M7":                  {"fcr":0x04, "fcw":None, "address":0x116F, "scale":1, "bias":0, "round":0},
            "CBAL_M8":                  {"fcr":0x04, "fcw":None, "address":0x117F, "scale":1, "bias":0, "round":0},
            "CBAL_M9":                  {"fcr":0x04, "fcw":None, "address":0x118F, "scale":1, "bias":0, "round":0},
            "CBAL_M10":                 {"fcr":0x04, "fcw":None, "address":0x119F, "scale":1, "bias":0, "round":0},
            "CBAL_M11":                 {"fcr":0x04, "fcw":None, "address":0x11AF, "scale":1, "bias":0, "round":0},
            "CBAL_M12":                 {"fcr":0x04, "fcw":None, "address":0x11BF, "scale":1, "bias":0, "round":0},
            "CBAL_M13":                 {"fcr":0x04, "fcw":None, "address":0x11CF, "scale":1, "bias":0, "round":0},
            "CBAL_M14":                 {"fcr":0x04, "fcw":None, "address":0x11DF, "scale":1, "bias":0, "round":0},
            "CBAL_M15":                 {"fcr":0x04, "fcw":None, "address":0x11EF, "scale":1, "bias":0, "round":0},
            "CBAL_M16":                 {"fcr":0x04, "fcw":None, "address":0x11FF, "scale":1, "bias":0, "round":0},
            ## Read and Write Coil (bit Type) (Don't Have "scale", "bias", and "round")
            "Output_Contactor_Coil":    {"fcr":0x01, "fcw":0x05, "address":0x0100, "scale":1, "bias":0, "round":0, "param": 0b0},
            "Cell_Balance_Coil":        {"fcr":0x01, "fcw":0x05, "address":0x0101, "scale":1, "bias":0, "round":0, "param": 0b0},
            "Shutdown_Coil":            {"fcr":0x01, "fcw":0x05, "address":0x0108, "scale":1, "bias":0, "round":0, "param": 0b0},
            "Reset_Coil":               {"fcr":0x01, "fcw":0x05, "address":0x0109, "scale":1, "bias":0, "round":0, "param": 0b0},
            ## Read and Write Hold Register (str Type)
            "CBCMU":                    {"fcr":0x03, "fcw":0x06, "address":0x2100, "scale":1, "bias":0, "round":0, "param": 0x0000},
            "CBCEL":                    {"fcr":0x03, "fcw":0x06, "address":0x2101, "scale":1, "bias":0, "round":0, "param": 0x0000}, # Size is 2 Bytes and each bit is represent each cell in a module (1-12); 0 or 1; 123456789ABC0000
            "CBV":                      {"fcr":0x03, "fcw":0x06, "address":0x2102, "scale":1/1000, "bias":0, "round":0, "param": 0x0000}, # Control cell balance active when the difference is more than or equal to this parameter
            "CBVDIF":                   {"fcr":0x03, "fcw":0x06, "address":0x2103, "scale":1/1000, "bias":0, "round":0, "param": 0x0000}  # Control cell balance non-active when the difference is less than this parameter            }
        }
        # Used to shift the Modbus memory address for some devices
        for key in self._memory_dict: self._memory_dict[key]["address"] += shift
        # Extra calculation for parameters/data that is not readily available from Modbus, add if needed
        self._extra_calc = {
            ## compile
            "Cell_Voltage_M1":      {"compile":["Voltage_M1_C1","Voltage_M1_C2","Voltage_M1_C3","Voltage_M1_C4","Voltage_M1_C5","Voltage_M1_C6","Voltage_M1_C7","Voltage_M1_C8","Voltage_M1_C9","Voltage_M1_C10","Voltage_M1_C11","Voltage_M1_C12"]},
            "Cell_Voltage_M2":      {"compile":["Voltage_M2_C1","Voltage_M2_C2","Voltage_M2_C3","Voltage_M2_C4","Voltage_M2_C5","Voltage_M2_C6","Voltage_M2_C7","Voltage_M2_C8","Voltage_M2_C9","Voltage_M2_C10","Voltage_M2_C11","Voltage_M2_C12"]},
            "Cell_Voltage_M3":      {"compile":["Voltage_M3_C1","Voltage_M3_C2","Voltage_M3_C3","Voltage_M3_C4","Voltage_M3_C5","Voltage_M3_C6","Voltage_M3_C7","Voltage_M3_C8","Voltage_M3_C9","Voltage_M3_C10","Voltage_M3_C11","Voltage_M3_C12"]},
            "Cell_Voltage_M4":      {"compile":["Voltage_M4_C1","Voltage_M4_C2","Voltage_M4_C3","Voltage_M4_C4","Voltage_M4_C5","Voltage_M4_C6","Voltage_M4_C7","Voltage_M4_C8","Voltage_M4_C9","Voltage_M4_C10","Voltage_M4_C11","Voltage_M4_C12"]},
            "Cell_Voltage_M5":      {"compile":["Voltage_M5_C1","Voltage_M5_C2","Voltage_M5_C3","Voltage_M5_C4","Voltage_M5_C5","Voltage_M5_C6","Voltage_M5_C7","Voltage_M5_C8","Voltage_M5_C9","Voltage_M5_C10","Voltage_M5_C11","Voltage_M5_C12"]},
            "Cell_Voltage_M6":      {"compile":["Voltage_M6_C1","Voltage_M6_C2","Voltage_M6_C3","Voltage_M6_C4","Voltage_M6_C5","Voltage_M6_C6","Voltage_M6_C7","Voltage_M6_C8","Voltage_M6_C9","Voltage_M6_C10","Voltage_M6_C11","Voltage_M6_C12"]},
            "Cell_Voltage_M7":      {"compile":["Voltage_M7_C1","Voltage_M7_C2","Voltage_M7_C3","Voltage_M7_C4","Voltage_M7_C5","Voltage_M7_C6","Voltage_M7_C7","Voltage_M7_C8","Voltage_M7_C9","Voltage_M7_C10","Voltage_M7_C11","Voltage_M7_C12"]},
            "Cell_Voltage_M8":      {"compile":["Voltage_M8_C1","Voltage_M8_C2","Voltage_M8_C3","Voltage_M8_C4","Voltage_M8_C5","Voltage_M8_C6","Voltage_M8_C7","Voltage_M8_C8","Voltage_M8_C9","Voltage_M8_C10","Voltage_M8_C11","Voltage_M8_C12"]},
            "Cell_Voltage_M9":      {"compile":["Voltage_M9_C1","Voltage_M9_C2","Voltage_M9_C3","Voltage_M9_C4","Voltage_M9_C5","Voltage_M9_C6","Voltage_M9_C7","Voltage_M9_C8","Voltage_M9_C9","Voltage_M9_C10","Voltage_M9_C11","Voltage_M9_C12"]},
            "Cell_Voltage_M10":     {"compile":["Voltage_M10_C1","Voltage_M10_C2","Voltage_M10_C3","Voltage_M10_C4","Voltage_M10_C5","Voltage_M10_C6","Voltage_M10_C7","Voltage_M10_C8","Voltage_M10_C9","Voltage_M10_C10","Voltage_M10_C11","Voltage_M10_C12"]},
            "Cell_Voltage_M11":     {"compile":["Voltage_M11_C1","Voltage_M11_C2","Voltage_M11_C3","Voltage_M11_C4","Voltage_M11_C5","Voltage_M11_C6","Voltage_M11_C7","Voltage_M11_C8","Voltage_M11_C9","Voltage_M11_C10","Voltage_M11_C11","Voltage_M11_C12"]},
            "Cell_Voltage_M12":     {"compile":["Voltage_M12_C1","Voltage_M12_C2","Voltage_M12_C3","Voltage_M12_C4","Voltage_M12_C5","Voltage_M12_C6","Voltage_M12_C7","Voltage_M12_C8","Voltage_M12_C9","Voltage_M12_C10","Voltage_M12_C11","Voltage_M12_C12"]},
            "Cell_Voltage_M13":     {"compile":["Voltage_M13_C1","Voltage_M13_C2","Voltage_M13_C3","Voltage_M13_C4","Voltage_M13_C5","Voltage_M13_C6","Voltage_M13_C7","Voltage_M13_C8","Voltage_M13_C9","Voltage_M13_C10","Voltage_M13_C11","Voltage_M13_C12"]},
            "Cell_Voltage_M14":     {"compile":["Voltage_M14_C1","Voltage_M14_C2","Voltage_M14_C3","Voltage_M14_C4","Voltage_M14_C5","Voltage_M14_C6","Voltage_M14_C7","Voltage_M14_C8","Voltage_M14_C9","Voltage_M14_C10","Voltage_M14_C11","Voltage_M14_C12"]},
            "Cell_Voltage_M15":     {"compile":["Voltage_M15_C1","Voltage_M15_C2","Voltage_M15_C3","Voltage_M15_C4","Voltage_M15_C5","Voltage_M15_C6","Voltage_M15_C7","Voltage_M15_C8","Voltage_M15_C9","Voltage_M15_C10","Voltage_M15_C11","Voltage_M15_C12"]},
            "Cell_Voltage_M16":     {"compile":["Voltage_M16_C1","Voltage_M16_C2","Voltage_M16_C3","Voltage_M16_C4","Voltage_M16_C5","Voltage_M16_C6","Voltage_M16_C7","Voltage_M16_C8","Voltage_M16_C9","Voltage_M16_C10","Voltage_M16_C11","Voltage_M16_C12"]},
            "Module_Voltage":       {"compile":["Voltage_M1","Voltage_M2","Voltage_M3","Voltage_M4","Voltage_M5","Voltage_M6","Voltage_M7","Voltage_M8","Voltage_M9","Voltage_M10","Voltage_M11","Voltage_M12","Voltage_M13","Voltage_M14","Voltage_M15","Voltage_M16"]}, # Amps
            "Module_Temperature":   {"compile":[["Temperature_M1_1","Temperature_M2_1","Temperature_M3_1","Temperature_M4_1","Temperature_M5_1","Temperature_M6_1","Temperature_M7_1","Temperature_M8_1","Temperature_M9_1","Temperature_M10_1","Temperature_M11_1","Temperature_M12_1","Temperature_M13_1","Temperature_M14_1","Temperature_M15_1","Temperature_M16_1"],
                                                ["Temperature_M1_2","Temperature_M2_2","Temperature_M3_2","Temperature_M4_2","Temperature_M5_2","Temperature_M6_2","Temperature_M7_2","Temperature_M8_2","Temperature_M9_2","Temperature_M10_2","Temperature_M11_2","Temperature_M12_2","Temperature_M13_2","Temperature_M14_2","Temperature_M15_2","Temperature_M16_2"],
                                                ["Temperature_M1_3","Temperature_M2_3","Temperature_M3_3","Temperature_M4_3","Temperature_M5_3","Temperature_M6_3","Temperature_M7_3","Temperature_M8_3","Temperature_M9_3","Temperature_M10_3","Temperature_M11_3","Temperature_M12_3","Temperature_M13_3","Temperature_M14_3","Temperature_M15_3","Temperature_M16_3"]]} # Amps
            }

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
