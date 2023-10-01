"""
DS3231 RTC is connected to GP00(SDA), GP01(SCL), GP02(SQW)
LCD 1602 I2C is connected to GP06(SDA), GP07(SCL)
button_1 is connected to GP10 ---> Change time
button_2 is connected to GP11 ---> Set alarm
button_3 is connected to GP12 ---> Light / Turn OFF alarm
button_4 is connected to GP13 ---> Turn ON LCD
button_re is connected to GP05 ---> Change alarm
Rotary Encoder is connected to GP03(CLK), GP04(DT), GP05(SW)
WS2812 LED is connected to GP18(D1)
"""
import machine
import DS3231_with_alarm
import time
import utime
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd
from rotary_irq_rp2 import RotaryIRQ
import neopixel

# Initializing LCD_1602_I2C
I2C_ADDR     = 0x26
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
i2c = machine.I2C(1, sda=machine.Pin(6), scl=machine.Pin(7), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
# Initializing DS3231_RTC
I2C_PORT = 0
I2C_SDA = 0
I2C_SCL = 1
ALARM_PIN = 2
rtc = DS3231_with_alarm.ds3231(I2C_PORT,I2C_SCL,I2C_SDA)
# For alarm indication (will be changed later or not)
led_onboard = machine.Pin(25, machine.Pin.OUT)
buzzer = machine.Pin(22, machine.Pin.OUT)
# Buttons
button_1 = machine.Pin(10, machine.Pin.IN, machine.Pin.PULL_DOWN) # To set time
button_2 = machine.Pin(11, machine.Pin.IN, machine.Pin.PULL_DOWN) # To set alarm
button_3 = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_DOWN) # To turn ON the LED
button_4 = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_DOWN)
# Initializing Rotary_Encoder
rotary = RotaryIRQ(pin_num_clk=3, 
                  pin_num_dt=4, 
                  min_val=0, 
                  max_val=23,
                  incr=1,
                  reverse=True, 
                  range_mode=RotaryIRQ.RANGE_WRAP)
button_re = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

ws_pin = 18
led_num = 1
BRIGHTNESS = 0.9  # Adjust the brightness (0.0 - 1.0)
neoRing = neopixel.NeoPixel(machine.Pin(ws_pin), led_num)
# We will need this later in the code
w = ["FRI", "SAT", "SUN", "MON", "TUE", "WED", "THU"]
w1 = ["Friday","Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday"]

def get_time():    # To get time from the DS3231_RTC
    global date
    global time_00
    global weekday
    global t
    t = rtc.read_time()
    time_list = t.split()
    date  = time_list[0]
    time_00 = time_list[1]
    weekday = time_list[2]
    weekday_01 = w1.index(weekday) # We check what is at the index of "w1" and assign that index to weekday_01
    weekday = w[weekday_01]        # Then we check what is the element in "w" at that index and assign it to weekday
    return date, time_00, weekday

def change_time():    # To change time and date
    current_time = t.split() 
    
    date = current_time[0]
    time_00 = current_time[1]
    date_str = current_time[2]
    
    time_00 = time_00.split(":")
    set_hour = time_00[0]
    set_minute =time_00[1]
    set_second =time_00[2]
    
    set_WD = w1.index(date_str)    # # We check what is at the index of "w1" and assign that index to set_WD
    date = date.split("/")
    set_day = date[0]
    set_month = date[1]
    set_year = date[2]
    
    # Setting Time
    lcd.clear()
    time.sleep(0.1)
    lcd.move_to(4,0)
    lcd.putstr("Set Time")
    lcd.move_to(4,1)
    lcd.putstr("00:00:00")
    
    # Setting Hour
    rotary.set(min_val=0, max_val=23)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(4,1)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(4,1)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_hour = new_val
    
    #Setting Minute
    time.sleep(0.25)
    rotary.set(min_val=0, max_val=59)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(7,1)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(7,1)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_minute = new_val
    
    set_second = 00
    
    #Setting Date and Weekday
    lcd.clear()
    time.sleep(0.25)
    lcd.move_to(3,0)
    lcd.putstr("Set Date")
    lcd.move_to(6,1)
    lcd.putstr("00/00/00")
    
    #Setting Date
    rotary.set(min_val=0, max_val=6)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        set_weekday = w[new_val]
        lcd.move_to(2,1)
        time.sleep(0.15)
        lcd.putstr("   ")
        lcd.move_to(2,1)
        time.sleep(0.15)
        lcd.putstr(str(set_weekday))
        set_WD = w.index(set_weekday)
        set_WD = w1[set_WD]
        
    #Setting Month We set month first because to avoid any confusion while setting the day
    time.sleep(0.25)
    rotary.set(min_val=1, max_val=12)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(9,1)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(9,1)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_month = new_val
        
    #Setting Day Based on what month it is, we choose the no. of days
    time.sleep(0.25)
    month_31 = [1, 3, 5, 7, 8, 10, 12]
    month_30 = [4, 6, 9, 11]
    month_28 = [2]
    m31 = int(set_month) in month_31
    m30 = int(set_month) in month_30
    m28 = int(set_month) in month_28
    if m31:
        rotary.set(min_val=0, max_val=31)
    elif m30:
        rotary.set(min_val=0, max_val=30)
    elif m28:
        rotary.set(min_val=0, max_val=28)
                  
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(6,1)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(6,1)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_day = new_val
    
    #Setting Year Not acutally necesssary, but we might need it sometime in the future
    time.sleep(0.25)
    rotary.set(min_val=0, max_val=99)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(12,1)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(12,1)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_year = new_val
        
    # Change the time and date to a string which will be used by the RTC
    # print("%02x:%02x:%02x,%s,20%x-%02x-%02x" %(set_hour,set_minute,set_second,set_WD,set_year,set_month,set_day))
    # new_time = "%02x:%02x:%02x,%s,20%x-%02x-%02x" %(set_hour,set_minute,set_second,set_WD,set_year,set_month,set_day)
    lcd.clear()
    time.sleep(0.1)
    new_time = str(set_hour) + ":" + str(set_minute) + ":" + "0" + str(set_second) + "," + str(set_WD) + "," + "20" + str(set_year) + "-" + str(set_month) + "-" + str(set_day)
    print(new_time)
    rtc.set_time(new_time) # Send the new_time string to RTC to set the required time and date
    
    
def set_alarm_01():    # To set the alarms 01 and 02
    global alarm_time_01
    global alarm_time_02
    # alarm_01 = alarm_time_01.split(",")
    # time_01 = alarm_01.split(":")
    # set_hour1 = time_01[0]
    # set_minute1 = time_02[1]
    # alarm_02 = alarm_time_02.split(",")
    # time_02 = alarm_02.split(":")
    # set_hour2 = time_02[0]
    # set_minute2 = time_02[1]
    lcd.clear()
    time.sleep(0.1)
    lcd.move_to(0,0)
    lcd.putstr("Alarm 1: ")
    lcd.move_to(9,0)
    lcd.putstr("00:00")
    # lcd.putstr(set_hour1 + ":" + set_minute1)
    lcd.move_to(0,1)
    lcd.putstr("Alarm 2: ")
    lcd.move_to(9,1)
    lcd.putstr("00:00")
    # lcd.putstr(set_hour2 + ":" + set_minute2)
    
    # Setting Hour 01
    time.sleep(0.1)
    rotary.set(min_val=0, max_val=23)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(9,0)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(9,0)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_hour1 = new_val
        
    #Setting Minute 01
    time.sleep(0.25)
    rotary.set(min_val=0, max_val=59)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(12,0)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(12,0)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_minute1 = new_val
    
    set_second1 = 00
    
    time.sleep(0.1)
    alarm_time_01 = str(set_hour1) + ":" + str(set_minute1) + ":" + "0" + str(set_second1) + ",Sunday,2023-09-80"
    print(alarm_time_01) # Here we write the day as "80" because I choose the alarm to go off when hours, minutes, seconds match 
                         # If you want the alarm to go off at a particular day specify the day where "80" is written
    # Setting Hour 02
    time.sleep(0.25)
    rotary.set(min_val=0, max_val=23)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(9,1)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(9,1)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_hour2 = new_val
        
    #Setting Minute 02
    time.sleep(0.25)
    rotary.set(min_val=0, max_val=59)
    rotary.reset()
    while button_re.value() == 1:
        new_val = rotary.value()
        if new_val < 10:
            new_val = "0" + str(new_val)
        lcd.move_to(12,1)
        time.sleep(0.15)
        lcd.putstr("  ")
        lcd.move_to(12,1)
        time.sleep(0.15)
        lcd.putstr(str(new_val))
        set_minute2 = new_val
    
    set_second2 = 00
    
    lcd.clear()
    time.sleep(0.1)
    alarm_time_02 = str(set_hour2) + ":" + str(set_minute2) + ":" + "0" + str(set_second2) + ",Sunday,2023-09-80"
    print(alarm_time_02) # We also do the same thing to the day here
    
    rtc.set_alarm(alarm_time_01, alarm_time_02)
    
def alarm_ON(status):    # To know when the alarm has been triggered
    
    if status == 1:
        print("Alarm 01 triggered!")
        lcd.clear()
        time.sleep(0.1)
        lcd.move_to(4,0)
        lcd.putstr("Alarm 01")
        time.sleep(0.1)
    elif status == 2:
        print("Alarm 02 triggered!")
        lcd.clear()
        time.sleep(0.1)
        lcd.move_to(4,0)
        lcd.putstr("Alarm 02")
        time.sleep(0.1)
    elif status == 3:
        print("Both Alarms triggered!")
        lcd.clear()
        time.sleep(0.1)
        lcd.move_to(1,0)
        lcd.putstr("Alarm 01 & 02")
        time.sleep(0.1)
    while button_3.value() != 1:
        led_onboard.toggle()
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 100:
            buzzer.toggle()
            time.sleep_us(100)
        buzzer.value(0)
        time.sleep(0.1)
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 200:
            buzzer.toggle()
            time.sleep_us(100)
        buzzer.value(0)
        time.sleep(0.2)
    lcd.clear()
     
def neo():
    time.sleep(0.1)
    while button_3.value() == 0:
        color = (255, 255, 255)
        r, g, b = color
        r = int(r * BRIGHTNESS)
        g = int(g * BRIGHTNESS)
        b = int(b * BRIGHTNESS)
        color = (r, g, b)
        neoRing.fill(color)
        neoRing.write()
        time.sleep(0.1)
    r = int(0)
    g = int(0)
    b = int(0)
    color = (r, g, b)
    neoRing.fill(color)
    neoRing.write()
    time.sleep(0.5)
        
while True:
    if button_4.value() == 1:
        lcd.backlight_on()
        lcd.display_on()
        i = 0
        while i <= 10:
            print(get_time())
            lcd.move_to(4,0)
            lcd.putstr(time_00)
            lcd.move_to(2,1)
            lcd.putstr(weekday)
            lcd.move_to(6,1)
            lcd.putstr(date)
            if button_1.value() == 1:
                change_time()
            if button_2.value() == 1:
                set_alarm_01()
            if button_3.value() == 1:
                time.sleep(0.25)
                neo()
            time.sleep(0.7)
            i += 1
    elif button_4.value() == 0:
        lcd.display_off()
        lcd.backlight_off()
        status = rtc.check_alarm()
        if status != 0:
            alarm_ON(status)
        time.sleep(0.5)
