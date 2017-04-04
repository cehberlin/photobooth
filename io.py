#!/usr/bin/python

import RPi.GPIO as GPIO

#configuration

BUTTON_1 = 23
BUTTON_2 = 25
BUTTON_3 = 16
BUTTON_4 = 21

LED_1 = 18
LED_2 = 24
LED_3 = 12
LED_4 = 20


#setup

leds = [LED_1,LED_2,LED_3,LED_4]
buttons = [BUTTON_1,BUTTON_2,BUTTON_3,BUTTON_4]

GPIO.setmode(GPIO.BCM)

GPIO.setup(buttons, GPIO.IN)

GPIO.setup(leds, GPIO.OUT)

GPIO.output(leds, GPIO.LOW)

#test routine

while True:
    if GPIO.input(BUTTON_1) == GPIO.LOW:
        print('Button1')
        GPIO.output(LED_1, GPIO.HIGH)
    else:
        GPIO.output(LED_1, GPIO.LOW)
    if GPIO.input(BUTTON_2) == GPIO.LOW:
        print('Button2')
        GPIO.output(LED_2, GPIO.HIGH)
    else:
        GPIO.output(LED_2, GPIO.LOW)
    if GPIO.input(BUTTON_3) == GPIO.LOW:
        print('Button3')
        GPIO.output(LED_3, GPIO.HIGH)
    else:
        GPIO.output(LED_3, GPIO.LOW)
    if GPIO.input(BUTTON_4) == GPIO.LOW:
        print('Button4')
        GPIO.output(LED_4, GPIO.HIGH)
    else:
        GPIO.output(LED_4, GPIO.LOW)
        

GPIO.cleanup()

