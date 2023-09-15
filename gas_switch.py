import sys
import time
import RPi.GPIO as GPIO

# gpio pins of rockers - these correspond to reactors 1-3
rockers = [17, 18, 27]

# initialize gpio
GPIO.setmode(GPIO.BCM)
for i in rockers:
    GPIO.setup(i, GPIO.OUT)
    GPIO.output(i, GPIO.LOW)

def activate_rocker(num):
    '''Activates the indicated rocker and deactivates the others.'''
    if not num in range(len(rockers)):
        print('Invalid rocker number', num, file=sys.stderr)
        return

    # separate list into rockers to be closed and opened
    inactive_rockers = rockers.copy()
    rocker = inactive_rockers.pop(num) 

    GPIO.output(inactive_rockers, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(rocker, GPIO.HIGH)

def cleanup():
    GPIO.cleanup()
