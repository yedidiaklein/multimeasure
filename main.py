from machine import Pin, SoftI2C, ADC, Timer
from sht30 import SHT30 
import time
import ubinascii
from umqtt.simple import MQTTClient
import ujson
import gc

# Try to import WDT if available
try:
    from machine import WDT
    HAS_WDT = True
except ImportError:
    HAS_WDT = False
    print("WDT not available on this build")

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
    
    # Create fresh MQTT client for each send to avoid socket issues
    with open('config.json') as json_file:
        data = ujson.load(json_file)
    
    mqtt_client = MQTTClient("umqtt_client", data['mqtt'], data['mqttport'], data['mqttuser'], data['mqttpass'])
    
    try:
        mqtt_client.connect()
        topic = "homeassistant/sensor/multimeasure" + mac + "/" + name + "/config"
        mqtt_client.publish(topic, json)
        topic = "multimeasure/" + mac + "/" + name
        mqtt_client.publish(topic, value)
    finally:
        try:
            mqtt_client.disconnect()
        except:
            pass
        del mqtt_client
 
def timer_callback(timer):
    global rssi, sensor, error_count, wdt
    
    # Feed the watchdog to prevent reset (if available)
    if HAS_WDT and wdt:
        wdt.feed()
    
    # Collect garbage before starting
    gc.collect()
    print("Free memory:", gc.mem_free())
    
    try:
        # reconnect to network if needed
        mac_addr, rssi = wifi()
        
        # Temp and Humidity
        temperature, humidity = sensor.measure()
        light = lightdata.read()
        
        print("Sending data... T:", temperature, "H:", humidity, "L:", light)
        senddata("Temperature", "C", str(temperature))
        senddata("Humidity", "%", str(humidity))
        senddata("Illuminance", "lux", str(light))
        senddata("Signal_strength", "dBm", str(rssi))
        senddata("Battery", "%", "100")
        
        # Reset error count on success
        error_count = 0
        
    except Exception as e:
        print("Error in timer_callback:", str(e))
        error_count += 1
        
        # If too many consecutive errors, try to reset sensor
        if error_count >= 3:
            print("Too many errors, resetting sensor...")
            try:
                sensor.reset()
                time.sleep(1)
                error_count = 0
            except Exception as reset_error:
                print("Failed to reset sensor:", str(reset_error))
                # Recreate sensor object if reset fails
                try:
                    sensor = SHT30()
                    error_count = 0
                except:
                    print("Failed to recreate sensor")
        
        # If too many errors, let watchdog reset the device
        if error_count >= 5:
            print("Critical: Too many errors, waiting for watchdog reset...")
            while True:
                time.sleep(1)  # Don't feed watchdog, let it reset
    
    # Force garbage collection after each cycle
    gc.collect()

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

# Initialize error counter
error_count = 0

# Initialize watchdog timer if available (timeout in milliseconds)
# Will reset the device if not fed within 120 seconds
wdt = None
if HAS_WDT:
    try:
        wdt = WDT(timeout=120000)
        print("Watchdog timer enabled")
    except Exception as e:
        print("Failed to enable watchdog:", str(e))
        wdt = None

mac, rssi = wifi()

# Photo resistor on analog 0
lightdata = ADC(0)

# Initialize sensor once globally
sensor = SHT30()

# Enable garbage collection
gc.enable()
gc.collect()

print("Starting multimeasure... Free memory:", gc.mem_free())

# Send data on boot
timer_callback(0)

# Send data every minute (60000ms)
timer = Timer(-1)
timer.init(period=60000, mode=Timer.PERIODIC, callback=timer_callback)



