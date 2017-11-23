import os
import time
import sys
import Adafruit_DHT as dht
import paho.mqtt.client as mqtt
import json

# Data capture and upload interval in seconds. Less interval will eventually hang the DHT22.
INTERVAL=300
sensor_data = {'Temperatur': 0, 'Luftfeuchte': 0}
next_reading = time.time()
client = mqtt.Client()
client.username_pw_set("pimatic", "NtP2X7a6tDdSPhvT")
client.connect("192.168.178.10", 1883)

client.loop_start()

try:
    while True:
        invalid = False
        humidity,temperature = dht.read_retry(dht.DHT22, 5)
        humidity = round(humidity, 2)
        temperature = round(temperature, 2)
        print(u"Temperature: {:g}\u00b0C, Humidity: {:g}%".format(temperature, humidity))
        if(temperature < 50 and humidity <= 100):
            sensor_data['Temperatur'] = temperature
            sensor_data['Luftfeuchte'] = humidity
        else:
            invalid = True

        # Sending humidity and temperature data to ThingsBoard
        if(invalid == False):
            client.publish('/Wohnzimmer/DHT22', json.dumps(sensor_data), 1)
            INTERVAL = 300
        else:
            INTERVAL = 2

        next_reading += INTERVAL
        sleep_time = next_reading-time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
except (KeyboardInterrupt, SystemExit):
    print(" bye bye !")

client.loop_stop()
client.disconnect()
