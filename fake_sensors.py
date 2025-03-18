import random
import threading


class FakeBlueVCount:
    _vol = 0
    timer = None
    flowrate = 10
    current_flowrate = 10
    flowvar = 0.5  # standard deviation on flow rate
    delay = None
    quitting = False
    timer = None

    def __init__(self, flowrate=10, flowvar=0.5):
        self.delay = 60 / (flowrate / 0.6)
        self.flowvar = flowvar
        self.flowrate = self.current_flowrate = flowrate
        self.set_new_timer()

    def get_temp(self):
        return round(20.5 + random.random(), 1)

    def get_pressure(self):
        return round(1.013 + random.uniform(-0.06, 0.06), 3)

    def get_vol(self):
        return round(self._vol, 1)

    def set_new_timer(self):
        if self.timer is not None:
            self.timer.cancel()
        if not self.quitting:
            self.timer = threading.Timer(
                60 / (self.current_flowrate / 0.6), self.add_vol
            )
            self.timer.start()

    def add_vol(self):
        self._vol += 0.6
        self.current_flowrate = random.normalvariate(self.flowrate, self.flowvar)
        self.set_new_timer()


class FakeBlueVary:
    h2 = 70
    humidity = 1.0

    def __init__(self, h2=70):
        self.h2 = h2

    def get_h2(self):
        return random.gauss(self.h2, 3)

    def get_co2(self):
        return random.gauss(100 - self.h2, 3)

    def get_humidity(self):
        return random.gauss(self.humidity, 0.1)
