import os
import rrdtool

RRD_FILE = os.path.expanduser('~/rrd.db')
GRAPH_FILE = '/www/rrd.png' # make sure web server directory is writeable

def exists():
    return os.path.exists(RRD_FILE)

def create_rrd():
    '''Create a round robin database with the following fields:
    flow_1-3: Gauges, 10 min heartbeat, values 0-5000.
    h2_1-3: Gauges, 10 min heartbeat, values 0-200.
    co2_1-3: Gauges, 10 min heartbeat, values 0-200.
    
    Two RRAs are used:
    RRA #1: Last available value, 7 days of data available.
    RRA #2: Average value every 30 minutes, 7 days of data available.
    '''
    rrdtool.create(RRD_FILE, 
                   '--step', '300',
                    'DS:flow_1:GAUGE:600:0:5000',
                    'DS:flow_2:GAUGE:600:0:5000', 
                    'DS:flow_3:GAUGE:600:0:5000', 
                    'DS:h2_1:GAUGE:600:0:100', 
                    'DS:h2_2:GAUGE:600:0:100', 
                    'DS:h2_3:GAUGE:600:0:100', 
                    'DS:co2_1:GAUGE:600:0:100', 
                    'DS:co2_2:GAUGE:600:0:100', 
                    'DS:co2_3:GAUGE:600:0:100', 
                    'RRA:LAST:0:1:2016',
                    'RRA:AVERAGE:0.5:6:336')

def send_to_rrd(flows, h2, co2):
    '''Accepts three 3-membered lists as arguments, containing flows (in ml/min), and H2/CO2 concentrations (in %)
    for the three reactors.'''
    upd_string = 'N:' + \
                 str(flows[0]) +':'+ str(flows[1]) +':'+ str(flows[2]) +':'+ \
                 str(h2[0]) +':'+ str(h2[1]) +':'+ str(h2[2]) +':'+ \
                 str(co2[0]) +':'+ str(co2[1]) +':'+ str(co2[2])
    print(upd_string)
    rrdtool.update(RRD_FILE, 
                   upd_string)

def update_rrd_graph():
    def plot_flow(num, color): 
        return f"DEF:flow_{num}={RRD_FILE}:flow_{num}:AVERAGE", \
               f"LINE:flow_{num}#{color}:Reactor {num} flow", \
               f"GPRINT:flow_{num}:MIN:Min\\: %3.1lf", \
               f"GPRINT:flow_{num}:MAX:Max\\: %3.1lf", \
               f"GPRINT:flow_{num}:AVERAGE:Avg.\\: %3.1lf\\n"

    def plot_h2(num, color):
        return f"DEF:h2_{num}={RRD_FILE}:h2_{num}:AVERAGE", \
               f"LINE:h2_{num}#{color}:Reactor {num} H2  ", \
               f"GPRINT:h2_{num}:MIN:Min\\: %2.1lf", \
               f"GPRINT:h2_{num}:MAX:Max\\: %2.1lf", \
               f"GPRINT:h2_{num}:AVERAGE:Avg.\\: %2.1lf\\n"

    def plot_co2(num, color):
        return f"DEF:co2_{num}={RRD_FILE}:co2_{num}:AVERAGE", \
               f"LINE:co2_{num}#{color}:Reactor {num} CO2 ", \
               f"GPRINT:co2_{num}:MIN:Min\\: %2.1lf", \
               f"GPRINT:co2_{num}:MAX:Max\\: %2.1lf", \
               f"GPRINT:co2_{num}:AVERAGE:Avg.\\: %2.1lf\\n"

    a = [GRAPH_FILE,
         *plot_flow(1, 'FF8439'),
         *plot_flow(2, '00BA27'),
         *plot_flow(3, '3C65FF'),
         *plot_h2(1, 'CE2500'),
         *plot_h2(2, '00BA4B'),
         *plot_h2(3, '6409FF'),
         *plot_co2(1, 'C02500'),
         *plot_co2(2, '0EBA4B'),
         *plot_co2(3, '6A09FF'),
         "-u 100",
         "-l 0",
         "-w 600",
         "-h 400",
         '--start', 'N-7d',
         '--end', 'N',
         "-v Flow [ml/min] / H2 [%]"]
    rrdtool.graph(a)

