#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
from sim import logconf
import logging
from sim import SIM

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Execute the simulation.")
    #parser.add_argument("simargs", help="Simulation arguments (json)", type=str)
    #cmdargs = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, **logconf)

    #with open(cmdargs.simargs) as f:
    #    args = json.load(f)

    args = {'until': 20}

    sim = SIM()

    sim.setup(args)

    sim.run()

    sim.cleanup()

