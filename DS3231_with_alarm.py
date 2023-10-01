#!/usr/bin/python
# -*- coding: utf-8 -*-
from machine import Pin, I2C
import time
import binascii

#    the first version use i2c1
#I2C_PORT = 1
#I2C_SDA = 6
#I2C_SCL = 7

#    the new version use i2c0,if it dont work,try to uncomment the line 14 and comment line 17
#    it should solder the R3 with 0R resistor if want to use alarm function,please refer to the Sch file on waveshare Pico-RTC-DS3231 wiki
#    https://www.waveshare.net/w/upload/0/08/Pico-RTC-DS3231_Sch.pdf
I2C_PORT = 1
I2C_SDA = 2
I2C_SCL = 3

ALARM_PIN = 18


class ds3231(object):
#            13:45:00 Mon 24 May 2021
#  the register value is the binary-coded decimal (BCD) format
#               sec min hour week day month year
    NowTime = b'\x00\x45\x13\x02\x24\x05\x21'
    w1 = ["FRI", "SAT", "SUN", "MON", "TUE", "WED", "THU"];
    w = ["Friday","Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday"]
    address = 0x68
    start_reg = 0x00
    alarm1_reg = 0x07
    alarm2_reg = 0x0b
    control_reg = 0x0e
    status_reg = 0x0f
    
    def __init__(self,i2c_port,i2c_scl,i2c_sda):
        self.bus = I2C(i2c_port,scl=Pin(i2c_scl),sda=Pin(i2c_sda))

    def set_time(self,new_time):
        hour = new_time[0] + new_time[1]
        minute = new_time[3] + new_time[4]
        second = new_time[6] + new_time[7]
        week = "0" + str(self.w.index(new_time.split(",",2)[1])+1)
        year = new_time.split(",",2)[2][2] + new_time.split(",",2)[2][3]
        month = new_time.split(",",2)[2][5] + new_time.split(",",2)[2][6]
        day = new_time.split(",",2)[2][8] + new_time.split(",",2)[2][9]
        now_time = binascii.unhexlify((second + " " + minute + " " + hour + " " + week + " " + day + " " + month + " " + year).replace(' ',''))
        #print(binascii.unhexlify((second + " " + minute + " " + hour + " " + week + " " + day + " " + month + " " + year).replace(' ','')))
        #print(self.NowTime)
        self.bus.writeto_mem(int(self.address),int(self.start_reg),now_time)
    
    def read_time(self):
        t = self.bus.readfrom_mem(int(self.address),int(self.start_reg),7)
        second = t[0]&0x7F  #second
        minute = t[1]&0x7F  #minute
        hour = t[2]&0x3F  #hour
        weekday = self.w[t[3]-1]  #week
        day = t[4]&0x3F  #day
        month = t[5]&0x1F  #month
        year = t[6]  #year
        #print("%02x/%02x/%02x %02x:%02x:%02x %s" %(t[4],t[5],t[6],t[2],t[1],t[0],self.w[t[3]-1]))
        return("%02x/%02x/%02x %02x:%02x:%02x %s" %(t[4],t[5],t[6],t[2],t[1],t[0],self.w[t[3]-1]))
        
    
    def set_alarm(self,alarm_time_01, alarm_time_02):
        #    enable the alarm1_reg and alarm2_reg
        self.bus.writeto_mem(int(self.address),int(self.control_reg),b'\x07')
        #    convert to the BCD format
        hour1 = alarm_time_01[0] + alarm_time_01[1]
        minute1 = alarm_time_01[3] + alarm_time_01[4]
        second1 = alarm_time_01[6] + alarm_time_01[7]
        date1 = alarm_time_01.split(",",2)[2][8] + alarm_time_01.split(",",2)[2][9]
        now_time_01 = binascii.unhexlify((second1 + " " + minute1 + " " + hour1 +  " " + date1).replace(' ',''))
        #    write alarm time to alarm2 reg
        self.bus.writeto_mem(int(self.address),int(self.alarm1_reg),now_time_01)
        #    convert to the BCD format
        hour2 = alarm_time_02[0] + alarm_time_02[1]
        minute2 = alarm_time_02[3] + alarm_time_02[4]
        second2 = alarm_time_02[6] + alarm_time_02[7]
        date2 = alarm_time_02.split(",",2)[2][8] + alarm_time_02.split(",",2)[2][9]
        now_time_02 = binascii.unhexlify((minute2 + " " + hour2 +  " " + date2).replace(' ',''))
        #    write alarm time to alarm2 reg
        self.bus.writeto_mem(int(self.address),int(self.alarm2_reg),now_time_02)
                    
    def check_alarm(self):
        alarm_status = 0
        status = self.bus.readfrom_mem(self.address, self.status_reg, 1)
        if status == b'\x01':
            alarm_status = 1
        elif status == b'\x02':
            alarm_status = 2
        elif status == b'\x03':
            alarm_status = 3
        #    init the alarm pin
        self.alarm_pin = Pin(ALARM_PIN,Pin.IN,Pin.PULL_UP)
        #    set alarm irq
        self.alarm_pin.irq(lambda pin: print("Alarm is ON"), Pin.IRQ_FALLING)
        self.bus.writeto_mem(int(self.address), int(self.status_reg), b'\x00')
        return alarm_status