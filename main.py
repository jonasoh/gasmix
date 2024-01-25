import time
from statistics import mean
from collections import deque

import numpy as np

import db
import rrd
from gas_switch import activate_rocker, cleanup
from sensors import BlueVary, BlueVCount

VERBOSE = True

def get_vols(counters):
    return [counter.get_vol() for counter in counters]

# set up the rrd
rrd.create_rrds(rrd.missing_files())

# set up db
db.init()
try:
    dbver = db.queries.get_db_version()
except:
    db.rebuild_db()

# connect to sensors
bv = BlueVary('192.168.10.230')
bcs = [BlueVCount('/dev/ttyUSB0', 1), 
       BlueVCount('/dev/ttyUSB0', 2), 
       BlueVCount('/dev/ttyUSB0', 3)]
bcs[0].serial.baudrate = 38400
bcs[0].serial.stopbits = 2

# use this to keep track of which reactor is being measured
reactors = deque([0, 1, 2])

try:
    print('Gas logger and controller starting up.')
    while True:
        # outer loop: this is for measuring H2/CO2.
        # we need to use a relatively long time for this measurement
        r = reactors[0] # current reactor
        reactors.rotate(-1)
        activate_rocker(r)
        outerloopstart = time.monotonic()

        # inner loop: this is for measuring flows and data is collected every minute
        while time.monotonic() - outerloopstart < 60 * 60:
            loopstart = time.monotonic()
            init_vols = get_vols(bcs)

            while time.monotonic() - loopstart < 60:
                time.sleep(0.01)
            end_vols = get_vols(bcs)

            rrd.record_data(flows=(flows := [(x - y) / ((time.monotonic() - loopstart) / 60) for x, y in zip(end_vols, init_vols)]), reactor=r, h2=(h2 := bv.get_h2()), co2=(co2 := bv.get_co2()))
            if (VERBOSE):
                print(f"{flows=} {h2=} {co2=}")

            for cur_r in [0,1,2]:
                db.queries.insert_sensordata(read_time=int(time.time()),
                                    reactor=cur_r,
                                    vol=flows[cur_r],
                                    h2=h2 if cur_r == r else np.nan,
                                    co2=co2 if cur_r == r else np.nan,
                                    temp=bcs[cur_r].get_temp(),
                                    pressure=bcs[cur_r].get_pressure(),
                                    humidity=bv.get_humidity() if cur_r == r else np.nan,
                                    comment='')

finally:
    cleanup() # clean up GPIO
