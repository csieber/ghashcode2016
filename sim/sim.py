# -*- coding: utf-8 -*-

import time
import os
import json
import logging
#import networkx as nx
import numpy as np
import simpy

log = logging.getLogger(__name__)

def distance(f, t):
    return int(np.round(np.sqrt(np.power(np.abs(f._pos[0] - t._pos[0]), 2) + np.power(np.abs(f._pos[1] - t._pos[1]), 2))))

gl_warehouses = {}
gl_drones = {}
gl_products = {}
gl_orders = {}

class Warehouse(object):

    def __init__(self, env, id, pos, products):
        self._env = env
        self._id = id

        self._products = products

        self._pos = pos

        self._stock = {}

        for i in range(self._env.nr_product_T):
            self._stock[i] = 0

    def take(self, p_T, count):

        fa = (self._env.now, p_T, count, self._id)
        print("%1.f: Taking product %d %d times from warehouse %d." % fa)

        assert(self._stock[p_T] >= count)

        self._stock[p_T] -= count

    def stock(self, p_T):
        return self._stock[p_T]


class Order(object):

    def __init__(self, env, id, to, products):
        self._id = id
        self._pos = to
        self._env = env
        self._products = products


class Drone(object):

    def __init__(self, env, id, pos, capacity):
        self._env = env
        self._id = id
        self._capacity = capacity

        self._current_load = 0

        self._pos = pos

    def load(self, warehouse, p_T, count):

        fa = (self._env.now, self._id, warehouse._id, p_T, count)
        print("%.1f: Drone %d loading at warehouse %d product type %d %d times." % fa)

        self._env.commands.append("%dL%d%d%d" % fa[1:])

        # Flying
        yield self._env.timeout(distance(self, warehouse))

        # Delivering
        yield self._env.timeout(1)


    def unload(self, warehouse, p_T, count):

        fa = (self._env.now, self._id, warehouse._id, p_T, count)
        print("%.1f: Drone %d unloading at warehouse %d product type %d %d times." % fa)

        self._env.commands.append("%dU%d%d%d" % fa[1:])

        # Flying
        yield self._env.timeout(distance(self, warehouse))

        # Delivering
        yield self._env.timeout(1)


    def deliver(self, order, p_T, count):

        fa = (self._env.now, self._id, order._id, p_T, count)
        print("%.1f: Drone %d delivering for order %d product type %d %d of them." % fa)

        self._env.commands.append("%dD%d%d%d" % fa[1:])

        # Flying
        yield self._env.timeout(distance(self, order))

        # Delivering
        yield self._env.timeout(1)



class SIM(object):

    def __init__(self):

        self._env = simpy.Environment()

        self._commands = []

        setattr(self._env, 'commands', self._commands)

    def setup(self, args):

        self._args = args

        # Drone
        for idx, d in enumerate(self._args['drones']):
            gl_drones[idx] = Drone(self._env, idx, d['coords'], args['max_payload'])

        # Warehouses
        for idx, d in enumerate(self._args['warehouses']):
            gl_warehouses[idx] = Warehouse(self._env, idx, d['coords'], d['products'])

        # Orders
        for idx, d in enumerate(self._args['orders']):
            gl_orders[idx] = Order(self._env, idx, d['coords'], d['products'])

        # Sim Parameter
        setattr(self._env, 'gridsize', (args['cols'], args['rows']))
        setattr(self._env, 'until', args['time_limit'])
        setattr(self._env, 'nr_product_T', len(args['product_types']))

    def cleanup(self):

        log.debug("Saving commands file.")

        solutionf = open("solution.txt", 'w')

        print("%d" % len(self._commands), file=solutionf)

        for cmd in self._commands:
            print(cmd, file=solutionf)

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


