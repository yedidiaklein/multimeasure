# Multimeasure
This is the code for https://www.pcbway.com/project/shareproject/Smart_Home_Sensors_8a8fcac7.html

This hardware and software allow you to build a multi measure device that measure temperature, humidity and light - then send it to a MQTT server.

It can be easily integrated with HomeAssistant and other smart home tools that works with mqtt.

This project was done with my son Netanel.

# Install
* First of all you have to make the hardware, here is the devices and board : https://www.pcbway.com/project/shareproject/Smart_Home_Sensors_8a8fcac7.html
    * Install latest MicroPython on your Wemos.
    * Download from here : https://micropython.org/download/ESP8266_GENERIC/
    * Install in this way : esptool --port /dev/ttyUSB0 write_flash --flash_size=4MB -fm dio 0 Downloads/ESP8266_GENERIC-....
* Copy config-example.json to config.json, edit it with your wifi and mqtt settings.
* Copy software to your wemos.
    * ampy --port=/dev/ttyUSB0 put main.py
    * ampy --port=/dev/ttyUSB0 put lib
    * ampy --port=/dev/ttyUSB0 put config.json
* Reboot the wemos and check your mqtt.

# Credits
* Sht30 code is based on Roberto Sánchez work from https://github.com/rsc1975/micropython-sht30
* Mqtt code is from https://github.com/micropython/micropython-lib

