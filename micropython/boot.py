from time import sleep_ms, ticks_ms
from machine import I2C, Pin
from esp8266_i2c_lcd import I2cLcd
import time
import network
import si7021
import urequests as request
import json
DEFAULT_I2C_ADDR = 0x27
i2c = I2C(scl=Pin(2), sda=Pin(0), freq=100000)
lcd = I2cLcd(i2c, DEFAULT_I2C_ADDR, 2, 16)

id = ''
apikey = ''
ssdi = ''
password = ''

def init():
    with open("config.json", "r") as jsonfile:
        data = json.load(jsonfile) # Reading the file
        print("Read successful")
        jsonfile.close()
    apikey = data['apikey']   
    id = data['id']
    ssdi = data['ssdi']
    password = data['password']
    return apikey, id, ssdi, password

def connect(ssdi, password):
    
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssdi, password)
    print(station.isconnected())
    print(station.ifconfig())
    lcd.putstr("Connected")
    lcd.putstr("IP : ")
    time.sleep(3)
    ping = request.get('')
    if ping.content == "pong":
        lcd.clear()
        lcd.putstr("API UP")
        time.sleep(2)
        lcd.clear()
        lcd.putstr("Starting")
        time.sleep(2)
    else: 
        lcd.clear()
        lcd.putstr("API DOWN")
        exit(1)

def getdata(id, apikey):       
        lcd.clear()
        lcd.putstr("Getting data...")
        temp_sensor = si7021.Si7021(i2c)
        # print('Serial:              {value}'.format(value=temp_sensor.serial))
        # print('Identifier:          {value}'.format(value=temp_sensor.identifier))
        # print('Temperature:         {value}'.format(value=temp_sensor.temperature))
        # print('Relative Humidity:   {value}'.format(value=temp_sensor.relative_humidity))
        temps = []
        humis = []
        while i <= 5:
            i = 1
            i = i + 1
            temps.append(temp_sensor.temperature)
            humis.append(temp_sensor.humidity)
        temp = sum(temps)/len(temps)
        humi = sum(humis)/len(humis)
        lcd.clear()
        lcd.putstr('Temp:  {value}'.format(value=temp))
        lcd.putstr('Hum:   {value}'.format(value=humi))
        try:
            request.post("http://localhost:5010/post/sonde/%s/%s/%s/%s", id, apikey, temp, humi)
        except request.Error() as err:
            lcd.clear()
            lcd.putstr('Error failed send data')
            print('Failed send data' + err)
            exit()


if __name__ == '__main__':
    try:
        init()
    except init.Error() as err:
        print('Error init ' + err)
    try:
        connect(ssdi, password)
    except connect.Error() as err:
        print('Error connecting ' + err)
    while True:
        getdata(id, apikey)
        time.sleep(60)