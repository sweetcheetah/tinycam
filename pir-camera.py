#!/usr/bin/env python3
"""TinyCam"""
import time
import logging
from picamera2 import Picamera2

import RPi.GPIO as GPIO

SENSOR_1_PIN = 4
 
GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_1_PIN, GPIO.IN)
 
def motion1(channel):
    print('Movement on 1')
 
try:
    GPIO.add_event_detect(SENSOR_1_PIN , GPIO.RISING, callback=motion1)

    while True:
        time.sleep(100)
except KeyboardInterrupt:
    print("Finish...")
GPIO.cleanup()
