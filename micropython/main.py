from time import sleep_ms, ticks_ms
from machine import Pin, I2C
from esp8266_i2c_lcd import I2cLcd
import time
import network
import si7021
import urequests as requests
import json
DEFAULT_I2C_ADDR = 0x27
i2c = I2C(scl=Pin(2), sda=Pin(0), freq=100000)
lcd = I2cLcd(i2c, DEFAULT_I2C_ADDR, 2, 16)

id = ''
apikey = ''
ssid = ''
password = ''
ip = ''

def init():
    with open("config.json") as jsonfile:
        data = json.load(jsonfile) # Reading the file
        print("Read successful")   
        print(data)
        print(data['ip'])
        ip = data['ip']
        apikey = data['apikey']   
        id = data['id']
        ssid = data['ssid']
        password = data['password']
        print(ssid)
        print(password)
        lcd.putstr("OK")
    return {'ip':ip, 'apikey':apikey, 'id':id, 'ssid':ssid, 'password':password}

def connect(ip, ssid, password):
    print(ip)
    print(ssid)
    print(password)
    station = network.WLAN(network.STA_IF)
    while station.isconnected() == False:
        station.active(True)
        station.connect(ssid, password)
        print(station.isconnected())
    print(station.ifconfig())
    lcd.clear()
    lcd.putstr("Connected")
    time.sleep(2)
    ipp = station.ifconfig()
    lcd.clear()
    print(ipp[0])
    lcd.clear()
    lcd.putstr("IP : \n" + ipp[0])
    time.sleep(2)
    print(ip)
    ping = requests.get('http://' + ip + ':5010/ping')
    print(ping.status_code)
    if ping.status_code == 200:
        lcd.clear()
        lcd.putstr("API UP")
        time.sleep(2)
        lcd.clear()
    else: 
        lcd.clear()
        lcd.putstr("API DOWN")
        exit(1)

def getdata(id, apikey, ip):
        lcd.clear()
        lcd.putstr("Getting data...")
        time.sleep(2)
        temp_sensor = si7021.Si7021(i2c)
        # print('Serial:              {value}'.format(value=temp_sensor.serial))
        # print('Identifier:          {value}'.format(value=temp_sensor.identifier))
        # print('Temperature:         {value}'.format(value=temp_sensor.temperature))
        # print('Relative Humidity:   {value}'.format(value=temp_sensor.relative_humidity))
        temps = []
        humis = []
        i = 1
        while i < 6:
            i = i + 1
            temps.append(temp_sensor.temperature)
            humis.append(temp_sensor.relative_humidity)
        temp = sum(temps)/len(temps)
        humi = sum(humis)/len(humis)
        lcd.clear()
        lcd.putstr('Temp: {value} C'.format(value=temp))
        lcd.putstr('\n HR:   {value} %'.format(value=humi))
        time.sleep(5)
        url = "http://" + ip + ":5010/post/sonde"
        print(url)
        datas = {"id":id,"key":apikey,"temp":str(temp), "humi":str(humi)}
        print(datas)
        test = json.dumps(datas).encode('utf-8')
        print(test)
        headers = {'Content-Type': 'application/json'}
        send = requests.post(url, data=test, headers=headers)
        print(send.status_code)
        if send.status_code == 201:
            lcd.clear()
            lcd.putstr('Envoie des data ok')
            time.sleep(2)
            lcd.clear()
            lcd.putstr('Temp: {value} C'.format(value=temp))
            lcd.putstr('\n HR:   {value} %'.format(value=humi))
        else:
            lcd.clear()
            lcd.putstr("Erreur dans l'envoie des data")
            time.sleep(5)
            lcd.clear()
            lcd.putstr('Temp: {value} C '.format(value=temp))
            lcd.putstr('\n HR:   {value} %'.format(value=humi))


if __name__ == '__main__':
    try:
        config=init()
        
        lcd.clear()
        lcd.putstr("Starting.")
        time.sleep(2)
        lcd.clear()
        lcd.putstr("Starting..")
        time.sleep(2)
        lcd.clear()
        lcd.putstr("Starting...")
        time.sleep(2)
        lcd.clear()
        connect(config['ip'], config['ssid'], config['password'])
    except:
        print('Error init')
        
    while True:
         getdata(config['id'], config['apikey'], config['ip'])
         time.sleep(60)