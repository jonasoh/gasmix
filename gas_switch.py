import sys
import time
import RPi.GPIO as GPIO

# gpio pins of rockers - these correspond to reactors 1-3
rockers = [17, 18, 27]

# initialize gpio
GPIO.setmode(GPIO.BCM)
GPIO.setup(rockers, GPIO.OUT, initial=GPIO.LOW)

def activate_rocker(num):
    '''Activates the indicated rocker and deactivates the others.'''
    if not num in range(len(rockers)):
        print('Invalid rocker number', num, file=sys.stderr)
        return

    output = [GPIO.LOW] * 3
    output[num] = GPIO.HIGH
    GPIO.output(rockers, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(rockers, output)


def cleanup():
    GPIO.output(rockers, GPIO.LOW)
    GPIO.cleanup()
