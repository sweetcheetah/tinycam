#!/usr/bin/env python3
"""TinyCam"""
import time
import logging
from picamera2 import Picamera2

import RPi.GPIO as GPIO

SENSOR_1_PIN = 21
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_1_PIN, GPIO.IN)
 
def motion1(channel):
    logging.info('Movement on 1')

def capture_image():
    ...

def capture_video():
    ...
 
try:
    GPIO.add_event_detect(SENSOR_1_PIN , GPIO.RISING, callback=motion1)

    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ...
GPIO.cleanup()
