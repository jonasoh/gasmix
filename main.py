import os
import time
import argparse
from collections import deque

import numpy as np

import db
import rrd
from gas_switch import activate_rocker, cleanup
from sensors import BlueVary, BlueVCount

print("Gas logger and controller starting up.")

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument(
    "-c",
    "--cycle-length",
    type=int,
    default=60,
    help='Set CO2/H" measuring cycle length (default: 60)',
)
parser.add_argument(
    "-d",
    "--device",
    type=str,
    default=None,
    help="Device entry for the USB to RS485 adapter (default: first /dev/ttyUSB* entry)",
)
parser.add_argument(
    "-n",
    "--num-reactors",
    type=int,
    default=3,
    choices=range(1, 4),  # Allows values 1, 2, or 3
    help="Number of reactors to track (default: 3, min: 1, max: 3)",
)
args = parser.parse_args()

VERBOSE = args.verbose
CYCLE_LENGTH = args.cycle_length
NUM_REACTORS = args.num_reactors


def get_vols(counters):
    return [counter.get_vol() for counter in counters]


# set up the rrd
rrd.create_rrds(rrd.missing_files())

# set up db
db.init()
if not os.path.exists(db.DB_FILE):
    db.rebuild_db()

# connect to sensors
if not args.device:
    devs = []
    with os.scandir("/dev") as d:
        for entry in d:
            if entry.name.startswith("ttyUSB"):
                devs.append("/dev/" + entry.name)
    if devs:
        USB_DEV = sorted(devs)[0]
    else:
        raise IOError("No USB device found for RS485 communication.")
else:
    USB_DEV = args.device

assert os.access(
    USB_DEV, mode=os.R_OK | os.W_OK
), f"USB device ({USB_DEV}) not accessible."
print(f"Using {USB_DEV} for serial communication.")

bv = BlueVary("192.168.10.230")
bcs = [BlueVCount(USB_DEV, 1), BlueVCount(USB_DEV, 2), BlueVCount(USB_DEV, 3)]
bcs[0].serial.baudrate = 38400
bcs[0].serial.stopbits = 2

# use this to keep track of which reactor is being measured
reactors = deque(range(NUM_REACTORS))

try:
    while True:
        # outer loop: this is for measuring H2/CO2.
        # we need to use a relatively long time for this measurement (settable via --cycle-length)
        r = reactors[0]  # reactor currently being sampled
        reactors.rotate(-1)
        activate_rocker(r)
        outerloopstart = time.monotonic()

        while time.monotonic() - outerloopstart < CYCLE_LENGTH * 60:
            # inner loop: this is for measuring flows. data is collected roughly every minute.
            loopstart = time.monotonic()
            init_vols = get_vols(bcs)

            while time.monotonic() - loopstart < 60:
                time.sleep(0.01)
            end_vols = get_vols(bcs)

            rrd.record_data(
                flows=(
                    flows := [
                        (x - y) / ((time.monotonic() - loopstart) / 60)
                        for x, y in zip(end_vols, init_vols)
                    ]
                ),
                reactor=r,
                h2=(h2 := bv.get_h2()),
                co2=(co2 := bv.get_co2()),
            )
            if VERBOSE:
                print(f"{flows=} {h2=} {co2=}")

            for cur_r in range(NUM_REACTORS):
                db.queries.insert_sensordata(
                    id=None,
                    read_time=int(time.time()),
                    reactor=cur_r,
                    vol=flows[cur_r],
                    h2=h2 if cur_r == r else np.nan,
                    co2=co2 if cur_r == r else np.nan,
                    temp=bcs[cur_r].get_temp(),
                    pressure=bcs[cur_r].get_pressure(),
                    humidity=bv.get_humidity() if cur_r == r else np.nan,
                    comment="",
                )

finally:
    cleanup()  # clean up GPIO
