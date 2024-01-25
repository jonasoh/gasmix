import os
import rrdtool

RRD_DIR = os.path.expanduser('~/rrd')
RRD_FILES = [os.path.join(RRD_DIR, 'reactor' + str(i) + '.rrd') for i in range(3)]

os.makedirs(RRD_DIR, exist_ok=True)

def missing_files():
    return [f for f in RRD_FILES if not os.path.exists(f)]

# helper functions for generating the rrdtool command
def plot_flow(num, color): 
    return f"DEF:flow={RRD_FILES[num]}:flow:AVERAGE", \
            f"LINE2:flow#{color}:Flow (ml/min)\\n", \
            f"GPRINT:flow:MIN:Flow\\: Min\\: %3.1lf", \
            f"GPRINT:flow:MAX:Max\\: %3.1lf", \
            f"GPRINT:flow:AVERAGE:Avg.\\: %3.1lf ml/min"

def plot_h2(num, color):
    return f"DEF:h2={RRD_FILES[num]}:h2:AVERAGE", \
            f"LINE2:h2#{color}:H2 (%)"

def plot_co2(num, color):
    return f"DEF:co2={RRD_FILES[num]}:co2:AVERAGE", \
            f"LINE2:co2#{color}:CO2 (%)"

def create_rrds(files):
    '''Create round robin databases with the following fields:
    flow, h2, co2, with 3 minute heartbeats. For storing data every minute.
    
    Two RRAs are used:
    RRA #1: Last available value, 7 days of data available.
    RRA #2: Average value every 30 minutes, 7 days of data available.
    '''
    for file in files:
        rrdtool.create(file,
                        '--step', '60',
                        'DS:flow:GAUGE:180:0:5000',
                        'DS:h2:GAUGE:180:0:100', 
                        'DS:co2:GAUGE:600:0:100', 
                        'RRA:LAST:0:1:10080',
                        'RRA:AVERAGE:0.5:6:1680')

def record_data(flows, reactor, h2, co2):
    '''Record data to the RRD. Flows are logged for all reactors,
    H2 and CO2 data only for the current reactor.'''
    for i in range(3):
        upd_string = 'N:' + \
                     str(flows[i]) + ':' + \
                     (str(h2) if i == reactor else 'U') + ':' + \
                     (str(co2) if i == reactor else 'U')
        rrdtool.update(RRD_FILES[i], upd_string)

def custom_rrd_graph(reactor, duration, width=600, height=400):
    '''Plots an RRD graph spanning the specified duration (in hours).
    Returns a PNG graph as bytes.'''
    a = [*plot_h2(reactor, '2848FE'),
         *plot_co2(reactor, '4B7B5B'),
         *plot_flow(reactor, 'FF8439'),
         "-u 75",
         "-l -5",
         f"-w {width}",
         f"-h {height}",
         '--start', 'N-' + str(duration) + 'h',
         '--end', 'N',
         '--title', 'Reactor ' + str(reactor),
         "-v Flow [ml/min] / H2 [%] / CO2 [%]"]
    return rrdtool.graphv('-', a)
