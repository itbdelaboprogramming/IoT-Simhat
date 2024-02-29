"""
#title           :DAC8532.py
#description     :library for DAC8532 DAC IC
#author          :Nauval Chantika
#date            :2024/02/04
#version         :1.0
#usage           :Signal Processing
#notes           :
#python_version  :3.11.2
#==============================================================================
"""
import time
import spidev
import RPi.GPIO as GPIO

class DAC8532:
    def __init__(self,name,bus=0,device=1,cs_dac=23,A=0x30,B=0x34,DAC_MAX=65535,DAC_VREF=3.3):
        self._name = name
        self._cs_dac_pin = cs_dac
        self._SPI = spidev.SpiDev(bus, device)
        self._channel_A = A
        self._channel_B = B
        self.Value = [0, 0]
        self._DAC_Value_MAX = DAC_MAX
        self._DAC_VREF = DAC_VREF
        self.module_init()
    
    def DAC8532_Write_Data(self, Channel, Data):
        GPIO.output(self._cs_dac_pin, GPIO.LOW)#cs  0
        self._SPI.writebytes([Channel, Data >> 8, Data & 0xff])
        GPIO.output(self._cs_dac_pin, GPIO.HIGH)#cs  0
        
    def DAC8532_Out_Voltage(self, Channel, Voltage):
        if((Voltage <= self._DAC_VREF) and (Voltage >= 0)):
            temp = int(Voltage * self._DAC_Value_MAX / self._DAC_VREF)
            self.DAC8532_Write_Data(Channel, temp)
            
    def module_init(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        #GPIO.setup(self._rst_pin, GPIO.OUT)
        GPIO.setup(self._cs_dac_pin, GPIO.OUT)
        #GPIO.setup(self._cs_adc_pin, GPIO.OUT)
        #GPIO.setup(self._drdy_pin, GPIO.IN)
        #GPIO.setup(self._drdy_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._SPI.max_speed_hz = 20000
        self._SPI.mode = 0b01
        return 0;
  
### END OF FILE ###

