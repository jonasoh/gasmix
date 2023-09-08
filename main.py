import time
import math
from statistics import mean
from collections import deque

import db
import rrd
from gas_switch import activate_rocker
from sensors import BlueVary, BlueVCount

MEAS_TIME = 60 # time for averaging values and measuring flow
EQ_TIME = 20 # time for equilibrating the gas sensor
TIMEOUT = 15 # no gas during this time constitues a timeout

def nice_mean(vals):
    '''Like statistics.mean except it automatically filters out missing values.'''
    return mean([x for x in vals if isinstance(x, (int, float)) and not math.isnan(x)])

print('Gas logger and controller starting up.')

# set up the rrd
if not rrd.exists():
    rrd.create_rrd()

# set up connection to db
db.init()
try:
    dbver = db.queries.get_db_version()
except:
    db.rebuild_db()

# connect to sensors
bv = BlueVary('192.168.10.230')
bc = BlueVCount('/dev/ttyUSB0', 1)
bc.serial.baudrate = 38400
bc.serial.stopbits = 2

# use this to keep track of which reactor is being measured
reactors = deque([0, 1, 2])

h2 = ['U', 'U', 'U'] # rrdtool wants either 'U' or NaN for unknowns. i think it's ok to use 'U'.
co2 = ['U', 'U', 'U']
flows = ['U', 'U', 'U']

while True:
    r = reactors[0] # current reactor
    reactors.rotate(-1)
    activate_rocker(r)
    time.sleep(EQ_TIME)
    print('Measuring reactor', r)

    # wait for the flowmeter to click over to get more precise readings
    start = time.monotonic()
    val = bc.get_vol()
    while val == bc.get_vol() and time.monotonic() - start > TIMEOUT:
        # wait for volume tick or timeout
        time.sleep(0.1)

    lasttime = starttime = time.monotonic()
    startvol = bc.get_vol()
    raw_h2 = []
    raw_co2 = []
    lastvol = startvol
    while time.monotonic() - starttime < MEAS_TIME:
        if lastvol < bc.get_vol():
            lastvol = bc.get_vol()
            raw_h2.append(bv.get_h2())
            raw_co2.append(bv.get_co2())
            lasttime = time.monotonic() # time of last measurement
        time.sleep(0.1)
    elapsed = lasttime - starttime

    if lasttime > starttime: # there was at least one volume tick
        flows[r] = (bc.get_vol() - startvol)/(elapsed/60)
        h2[r] = nice_mean([raw_h2])
        co2[r] = nice_mean([raw_co2])
        comment = ''
    else:
        flows[r] = 0
        h2[r] = bv.get_h2() # XXX: these should be 'U' 
        co2[r] = bv.get_co2()
        comment = 'No volume'

    try:
        temp = bc.get_temp()
    except:
        temp = None

    try:
        hum = bv.get_humidity()
    except:
        hum = None

    try:
        pressure = bc.get_pressure()
    except:
        pressure = None

    db.queries.insert_sensordata(read_time=int(time.time()),
                                 reactor=r,
                                 vol=flows[r],
                                 h2=h2[r],
                                 co2=co2[r],
                                 temp=temp,
                                 pressure=pressure,
                                 humidity=hum,
                                 comment=comment)
    
    print(flows, h2, co2)

    if r == 2:
        rrd.send_to_rrd(flows, h2, co2)
        #rrd.update_rrd_graph()
        h2 = ['U', 'U', 'U']
        co2 = ['U', 'U', 'U']
        flows = ['U', 'U', 'U']
