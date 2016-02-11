# -*- coding: utf-8 -*-

import time
import os
import json
import logging
#import networkx as nx
import numpy as np
import simpy
#from simpy.events import AllOf
#from sim.resources import ASIC, NMS_Queue

log = logging.getLogger(__name__)

def distance(f, t):
    return np.sqrt(np.power(np.abs(f._pos[0] - t._pos[0]), 2) + np.power(np.abs(f._pos[1] - t._pos[1]), 2))

class Warehouse(object):

    def __init__(self, env, args):
        self._env = env
        self._id = args['id']

        self._products = args['products']

        self._pos = (0,0)

        #TODO: Generate availability



class Drone(object):

    def __init__(self, env, args):
        self._env = env
        self._id = args['id']
        self._capacity = args['capacity']

        self._pos = (0,0)

    def load(self):
        pass


class SIM(object):

    def __init__(self, args):

        self._env = simpy.Environment()
        self._args = args

        self._solutionf = open('solution.txt')

        setattr(self._env, 'solutionf', self._solutionf)

    def setup(self, G, args):
        pass

    def cleanup(self):
        pass

    def loop(self):

        return

        while True:
            pass
            # wh

            # yield self._env.timeout(self._conf_time)
            #self._env.process(self._nms.create_tunnel(from_id, to_id))

    def run(self):

        start = time.time()

        self._env.process(self.loop())

        self._env.run(until=self._args['until'])
        
        duration = time.time() - start
        
        log.info("Simulation took %.2fs." % duration)

        sim_stats = {'start': start, 'end': time.time()}

        with open(os.path.join(self._env.logdir._folder, 'sim_stats.json'), 'w') as fp:
            json.dump(sim_stats, fp)


