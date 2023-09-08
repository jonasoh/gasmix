import time
import RPi.GPIO as GPIO

# gpio pins of rockers - these correspond to reactors 1-3
rockers = [17, 18, 26]

# initialize gpio
GPIO.setmode(GPIO.BCM)
for i in rockers:
    GPIO.setup(i, GPIO.OUT)
    GPIO.output(i, GPIO.LOW)


def activate_rocker(num):
    '''Activates the indicated rocker and deactivates the others.'''
    if not num in range(len(rockers)):
        print('invalid rocker number')
        return
    
    # separate list into rockers to be closed and opened
    r_list = rockers.copy()
    rocker = r_list.pop(num) 

    GPIO.output(r_list, 0)
    GPIO.output(rocker, 1)


def cleanup():
    GPIO.cleanup()

