import RPi.GPIO as GPIO
import time
import os

# Setări GPIO
LED_VERDE = 17
LED_ROSU = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_ROSU, GPIO.OUT)

def este_conectat_la_wifi():
    raspuns = os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")
    return raspuns == 0

try:
    while True:
        if este_conectat_la_wifi():
            GPIO.output(LED_VERDE, GPIO.HIGH)
            GPIO.output(LED_ROSU, GPIO.LOW)
        else:
            GPIO.output(LED_VERDE, GPIO.LOW)
            GPIO.output(LED_ROSU, GPIO.HIGH)
        time.sleep(5)  # Verifică la fiecare 5 secunde
except KeyboardInterrupt:
    print("Script oprit de utilizator.")
finally:
    GPIO.cleanup()