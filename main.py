from machine import Pin, SoftI2C, ADC, Timer
from sht30 import SHT30 
import time
import ubinascii
from umqtt.simple import MQTTClient
import ujson

## functions
def senddata(name, unit, value):
    config = { "uniq_id": mac + "_" + name,
               "device_class": name,
               "name": name,
               "unit_of_meas": unit,
               "val_tpl": "{{ value_json }}",
               "stat_t": "multimeasure/" + mac + "/" + name,
               "dev": { "name": "multimeasure" + mac, "mdl": "Multimeasure", "sw": "0.9", "mf": "Yedidia", "ids": ["123"]}}
    json = ujson.dumps(config)
    try:
        mqtt.connect()
        topic = "homeassistant/sensor/multimeasure" + mac + "/" + name + "/config"
        mqtt.publish(topic, json)
        topic = "multimeasure/" + mac + "/" + name
        mqtt.publish(topic, value)
    finally:
        try:
            mqtt.disconnect()
        except:
            pass
 
def timer_callback(timer):
    global rssi
    try:
        # reconnect to network if needed
        mac_addr, rssi = wifi()
	    # Temp and Humidity
        sensor = SHT30()
        temperature, humidity = sensor.measure()
        light = lightdata.read()
        print("Sending data...")
        senddata("Temperature", "C", str(temperature))
        senddata("Humidity", "%", str(humidity))
        senddata("Illuminance", "lux", str(light))
        senddata("Signal_strength", "dBm", str(rssi))
        senddata("Battery", "%", "100")
    except Exception as e:
        print("Error in timer_callback:", str(e))
        try:
            sensor.reset()
        except:
            print("Failed to reset sensor")
        try:
            mqtt.disconnect()
        except:
            pass

def wifi():
    import network
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    
    # Get MAC address (always available)
    mac = ubinascii.hexlify(sta_if.config('mac')).decode()
    
    # Check if already connected
    if sta_if.isconnected():
        print("Already connected")
        rssi = sta_if.status('rssi')
        return mac, rssi
    
    # Need to reconnect
    print("Connecting to WiFi...")
    sta_if.active(False)
    time.sleep(2)
    sta_if.active(True)
    with open('config.json') as json_file:
        data = ujson.load(json_file)
        sta_if.connect(data['ssid'], data['psk'])
    
    # Wait for connection with timeout
    timeout = 30
    while not sta_if.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
        
    if not sta_if.isconnected():
        print("Failed to connect to WiFi")
        raise Exception("WiFi connection timeout")
        
    print("My IP is:")
    print(sta_if.ifconfig())
    rssi = sta_if.status('rssi')
    return mac, rssi

## Code

mac, rssi = wifi()

#MQTT Settings
with open('config.json') as json_file:
    data = ujson.load(json_file)
    mqtt = MQTTClient("umqtt_client", data['mqtt'], data['mqttport'], data['mqttuser'], data['mqttpass'])

# Photo resistor on analog 0
lightdata = ADC(0)

# Send data on boot
timer_callback(0)
# Send data every 3 minutes
timer = Timer(-1)
timer.init(period=60000, mode=Timer.PERIODIC, callback=timer_callback)



