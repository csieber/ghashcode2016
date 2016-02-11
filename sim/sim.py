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

gl_free_drones = {'resource': None}

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

        self._products = {}
        for i in range(self._env.nr_product_T):
            self._products[i] = sum([1 for p in products if p == i])

        self.served = False


class Drone(object):

    def __init__(self, env, id, pos, capacity):
        self._env = env
        self._id = id
        self._capacity = capacity

        self._current_load = 0

        self._pos = pos

        self.busy = False


    def space(self, p_T):
        return np.floor((self._capacity - self._current_load) / self._env.product_T[p_T])

    def put(self, p_T, count):
        self._current_load += self._env.product_T[p_T] * count

    def pull(self, p_T, count):
        self._current_load -= self._env.product_T[p_T] * count


    def serve(self, order, warehouses):

        order.served = True

        for w in warehouses:

            takes = {}

            for p_T, count in order._products.items():
                takes[p_T] = min(w.stock(p_T), count, self.space(p_T))

                print("loading..")
                yield self._env.process(self.load(w, p_T, takes[p_T]))
                print("done loading")

            for p_T, count in takes.items():
                yield self._env.process(self.deliver(order, p_T, count))


    def load(self, warehouse, p_T, count):

        warehouse._stock[p_T] -= count
        self.put(p_T, count)

        fa = (self._env.now, self._id, warehouse._id, p_T, count)
        print("%.1f: Drone %d loading at warehouse %d product type %d %d times." % fa)

        self._env.commands.append("%dL%d%d%d" % fa[1:])

        # Flying
        yield self._env.timeout(distance(self, warehouse))

        self._pos = warehouse._pos

        # Delivering
        yield self._env.timeout(1)


    def unload(self, warehouse, p_T, count):

        fa = (self._env.now, self._id, warehouse._id, p_T, count)
        print("%.1f: Drone %d unloading at warehouse %d product type %d %d times." % fa)

        self._env.commands.append("%dU%d%d%d" % fa[1:])

        # Flying
        yield self._env.timeout(distance(self, warehouse))

        self._pos = warehouse._pos

        # Delivering
        yield self._env.timeout(1)


    def deliver(self, order, p_T, count):

        order._products[p_T] -= count
        self.pull(p_T, count)

        fa = (self._env.now, self._id, order._id, p_T, count)
        print("%.1f: Drone %d delivering for order %d product type %d %d of them." % fa)

        self._env.commands.append("%dD%d%d%d" % fa[1:])

        # Flying
        yield self._env.timeout(distance(self, order))

        self._pos = order._pos

        # Delivering
        yield self._env.timeout(1)



class SIM(object):

    def __init__(self):

        self._env = simpy.Environment()

        self._commands = []

        setattr(self._env, 'commands', self._commands)

    def setup(self, args):

        self._args = args

        # Sim Parameter
        setattr(self._env, 'gridsize', (args['cols'], args['rows']))
        setattr(self._env, 'until', args['time_limit'])
        setattr(self._env, 'nr_product_T', len(args['product_types']))
        setattr(self._env, 'product_T', args['product_types'])

        # Drone
        for idx, d in enumerate(self._args['drones']):
            gl_drones[idx] = Drone(self._env, idx, d['coords'], args['max_payload'])

        # Warehouses
        for idx, d in enumerate(self._args['warehouses']):
            gl_warehouses[idx] = Warehouse(self._env, idx, d['coords'], d['products'])

        # Orders
        for idx, d in enumerate(self._args['orders']):
            gl_orders[idx] = Order(self._env, idx, d['coords'], d['products'])

        gl_free_drones['resource'] = simpy.Resource(self._env, capacity=len(gl_drones))

    def cleanup(self):

        log.debug("Saving commands file.")

        solutionf = open("solution.txt", 'w')

        print("%d" % len(self._commands), file=solutionf)

        for cmd in self._commands:
            print(cmd, file=solutionf)

    def loop(self):

        while True:

            print("%.1f: Requesting..." % self._env.now )
            request = gl_free_drones['resource'].request()
            yield request

            # gather all free drones
            free = [d for d in gl_drones.values() if not d.busy]

            # Go through all non served orders
            non_served = [tmp for tmp in gl_orders.values() if not tmp.served]

            order, drone, warehouses = next_order(free, non_served)

            print("Processing..")
            yield self._env.process(drone.serve(order, warehouses))
            print("Processing..DONE")

            gl_free_drones['resource'].release(request)


    def run(self):

        start = time.time()

        self._env.process(self.loop())

        self._env.run(until=self._env.until)
        
        duration = time.time() - start
        
        log.info("Simulation took %.2fs." % duration)


def next_order(free, non_served):

    costs = []

    for idx, order in enumerate(non_served[0:50]):

        cost_per_drone = [cost_of_order_per_drone(order, drone) for drone in free]

        costs.append((order,
                      free[np.argmin([x[1] for x in cost_per_drone])],
                      cost_per_drone[np.argmin([x[1] for x in cost_per_drone])]))

    tmp = [c[2][1] for c in costs]
    best = costs[np.argmin(tmp)]

    # order, drone, path
    return best[0], best[1], best[2][0]


def cost_of_order_per_drone(order, drone):

    path = []

    products = order._products.copy()

    warehouses = list(gl_warehouses.values())

    while sum(products.values()) > 0 and len(warehouses) > 0:

        w = warehouses[np.argmin([distance(w, order) for w in warehouses])]

        takes = {}

        for p_T, count in order._products.items():
            takes[p_T] = min(w.stock(p_T), count, drone.space(p_T))
            products[p_T] -= count

        warehouses.remove(w)
        path.append(w)

    if sum(products.values()) == 0:
        return path, 0
    else:
        return path, 1
