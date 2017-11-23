#!/usr/bin/python
import paho.mqtt.client as paho
import time
from threading import Thread
import json
import RPi.GPIO as GPIO
from backports import configparser

#GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

Shutters = []
GPIOData = []
UpdateAvalible = []

configPath = "/home/pi/Smarthome/Schaltserver/rollo.ini"

def RefreshState(RolloID, thisShutter, StateNow, finish):

    GPIOData[RolloID][3] = StateNow
    if(finish):
        with open(configPath, 'w') as configfile:
            config[thisShutter]['Shutter_now'] = str(StateNow)
            config.write(configfile)
            print("Job done")
            percent = 100 * StateNow / float(config[thisShutter]['shutter_movingtime'])
            client.publish(config[thisShutter]['mqttpub'], payload=str(percent), qos=0, retain=False)

def GPIOControl(RolloID, thisShutter):
    RolloID = int(RolloID)
    global UpdateAvalible
    while True :
        for element in GPIOData:
            if(element[0] == RolloID):
                now = float(element[3])
                target= float(element[4])
                GPIO_Down = element[2]
                GPIO_Up = element[1]
                timeout = 0
                GPIO.setup(int(GPIO_Down), GPIO.OUT)
                GPIO.setup(int(GPIO_Up), GPIO.OUT)
                GPIO.output(int(GPIO_Down), GPIO.HIGH)
                GPIO.output(int(GPIO_Up), GPIO.HIGH)
                move = ""
                if(now < target):
                    timeout = float((target - now))
                    move = "Down"
                if(now > target):
                    timeout = float((now - target))
                    move = "Up"
                while(UpdateAvalible[RolloID][0] == False):
                    if(timeout != 0.00 and move != ""):
                        if(move == "Up"):
                            #print ("GPIO Status of Pin" + GPIO_Down + ": OFF")
                            GPIO.output(int(GPIO_Down), GPIO.HIGH)
                            #print ("GPIO Status of Pin" + GPIO_Up + ": ON")
                            GPIO.output(int(GPIO_Up), GPIO.LOW)
                            if(timeout < 1):
                                time.sleep(timeout)
                                print("Movingtime: ", timeout)
                                timeout = 0
                            else:
                                print("Movingtime: ", timeout)
                                timeout = timeout - 1
                                RefreshState(RolloID, thisShutter, target + timeout, False)
                                time.sleep(1)
                        if(move == "Down"):
                            #print ("GPIO Status of Pin" + GPIO_Up + ": OFF")
                            GPIO.output(int(GPIO_Up), GPIO.HIGH)
                            #print ("GPIO Status of Pin" + GPIO_Down + ": ON")
                            GPIO.output(int(GPIO_Down), GPIO.LOW)
                            if(timeout < 1):
                                time.sleep(timeout)
                                print("Movingtime: ", timeout)
                                timeout = 0
                            else:
                                print("Movingtime: ", timeout)
                                timeout = timeout - 1
                                RefreshState(RolloID, thisShutter, target - timeout, False)
                                time.sleep(1)
                    elif(timeout == 0.00 and move == "Up"):
                            #print ("GPIO Status of Pin"  + GPIO_Up + ": OFF")
                            GPIO.output(int(GPIO_Up), GPIO.HIGH)
                            RefreshState(RolloID, thisShutter, target, True)
                            move = ""
                    elif(timeout == 0.00 and move == "Down"):
                            #print ("GPIO Status of Pin"  + GPIO_Down + ": OFF")
                            GPIO.output(int(GPIO_Down), GPIO.HIGH)
                            RefreshState(RolloID, thisShutter, target, True)
                            move =  ""
                    else:
                        time.sleep(2)
                #RefreshState(thisShutter, target)
                print("Checking for updates", int(RolloID))
        UpdateAvalible[RolloID][0] = False


def on_message(client, userdata, msg):
    print(msg.topic, msg.payload)
    for Shutter in Shutters:
        Shuttercounter = Shutters.index(Shutter)
        if(config[Shutter]['MQTT'] == msg.topic):
            NewPercent = int(msg.payload)
            if(NewPercent <= 100 or NewPercent >= 0):
                value = float(config[Shutter]['Shutter_movingtime']) * NewPercent / 100
                GPIOData[Shuttercounter][4] = value
                print (float(config[Shutter]['Shutter_movingtime']) * NewPercent / 100)
                UpdateAvalible[Shuttercounter][0] = True
                with open(configPath, 'w') as configfile:
                    config[Shutter]['Shutter_target'] = str(value)
                    config.write(configfile)
            else:
                print("Unknown message received")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print "Unexpected MQTT disconnection. Will auto-reconnect"

def on_connect(client, userdata, flags, rc):

    for Shutter in Shutters:
        client.subscribe(str(config[Shutter]['MQTT']), qos=1)
        print config[Shutter]['MQTT'] + " connected"

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(configPath)
    Shutters = config.sections()
    ShutterCounter = 0
    for Shutter in Shutters:
        #print config[Shutter]['MQTT']
        UpdateAvalible.append([False])
        Shuttercounter = Shutters.index(Shutter)
        print config[Shutter]['Shutter_target']
        GPIOData.append([Shuttercounter, config[Shutter]['GPIOup'], config[Shutter]['GPIOdown'], config[Shutter]['Shutter_now'], config[Shutter]['Shutter_target'], config[Shutter]['Shutter_movingtime']])
        print("Shutter Number " + str(Shuttercounter) +" registed")
        t = Thread(target=GPIOControl, args=(str(Shuttercounter), Shutter))
        #element[3], element[4], element[1], element[2]
        t.setName(str(Shuttercounter))
        t.setDaemon(True)
        t.start()
    #print GPIOData
    try:
            client = paho.Client()
            client.username_pw_set("pimatic", "NtP2X7a6tDdSPhvT")
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect("192.168.178.10", 1883)
            client.on_disconnect = on_disconnect
            client.loop_forever()


    except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            client.disconnect()
            GPIO.cleanup()
            print(" bye bye !")
