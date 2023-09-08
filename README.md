# Controller/logger for trickle bed reactors

Simple software to measure gas concentrations and flows from three TBRs using a single BlueVary/BlueVCount combination and three rocker valves. The software contains a logger/controller backend which measures the offgas streams from the reactors, averaging each reactor over 60 seconds, and a frontend which can display real-time data and export it to TSV.

![Example output](https://github.com/jonasoh/gasmix/assets/6480370/f13b3f41-663c-4bb1-b273-7b587dfbae62)
