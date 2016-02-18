# -*- coding: utf-8 -*-

import time
import logging
#import networkx as nx
import numpy as np
from load import load
from collections import Counter

log = logging.getLogger(__name__)

def distance(f, t):
    return int(np.round(np.sqrt(np.power(np.abs(f._pos[0] - t._pos[0]), 2) + np.power(np.abs(f._pos[1] - t._pos[1]), 2))))

gl_warehouses = {}
gl_drones = {}
gl_products = {}
gl_orders = {}

gl_free_drones = {'resource': None}

class Warehouse(object):

    def __init__(self, args, id, pos, products):

        self.args = args
        self.id = id

        self.pos = pos

        self.stock = {}

        for i in range(args['nr_product_T']):
            self.stock[i] = products[0]

    def take(self, p_T, count):

        print("Warehouse %d: Taking %d of product %d." % (self.id, p_T, count))

        assert(self.stock[p_T] >= count)

        self.stock[p_T] -= count

    def can_fulfil(self, order):

        count = Counter()

        for p_T, c in order._products.items():

            if self.stock[p_T] < c:
                count['not_available'] += 1
            else:
                count['available'] += 1

            count['count'] += 1

        print("Warehouse %d, Order %d: %d/%d available" % (self.id, order._id, count['available'], count['count']))

        return count

    def stock(self, p_T):
        return self.stock[p_T]


class Order(object):

    def __init__(self, args, id, to, products):
        self._id = id
        self._pos = to
        self.args = args

        self._products = {}

        for i in range(args['nr_product_T']):
            s = sum([1 for p in products if p == i])

            if s > 0:
                self._products[i] = s

        self.served = False


class Drone(object):

    def __init__(self, args, id, pos, capacity):
        self.args = args
        self._id = id
        self._capacity = capacity

        self._current_load = 0

        self._load = Counter()

        self._pos = pos

        self.busy = False

    def space(self, p_T):
        return np.floor((self._capacity - self._current_load) / self.args['product_T'][p_T])

    def put(self, p_T, count):

        print("Drone %d: Loading %d times product %d" % (self._id, count, p_T))
        assert(count > 0)

        self._load[p_T] += count

        self._current_load += self.args['product_T'][p_T] * count

        assert(self._current_load <= self._capacity)

        print("Drone %d: Utilization %d/%d" % (self._id, self._current_load, self._capacity))

    def pull(self, p_T, count):

        assert(count > 0)

        print("Drone %d: Unloading %d times product %d" % (self._id, p_T, count))

        self._load[p_T] -= count

        self._current_load -= self.args['product_T'][p_T] * count

        assert(self._current_load >= 0)

    def serve(self, order, warehouses):

        order.served = True

        for w in warehouses:

            takes = {}

            for p_T, count in order._products.items():

                print("We need %d times %d" % (count, p_T))

                print("Counters: Warehouse (%d) / Order (%d) / space left (%d)" % (w.stock(p_T), count, self.space(p_T)))
                takes[p_T] = min(w.stock(p_T), count, self.space(p_T))

                self.load(w, p_T, takes[p_T])

            for p_T, count in takes.items():
                self.deliver(order, p_T, count)


    def load(self, warehouse, p_T, count):

        warehouse._stock[p_T] -= count

        self.put(p_T, count)

        self.args['commands'].append("%d L %d %d %d" % (self._id, warehouse._id, p_T, count))

        self._pos = warehouse._pos


    def unload(self, warehouse, p_T, count):

        print("Drone %d unloading at warehouse %d product type %d %d times." % (self._id, warehouse._id, p_T, count))

        self.args['commands'].append("%d U %d %d %d" % (self._id, warehouse._id, p_T, count))

        self._pos = warehouse._pos


    def deliver(self, order, p_T, count):

        order._products[p_T] -= count
        self.pull(p_T, count)

        fa = (self._id, order._id, p_T, count)
        print("Drone %d delivering for order %d product type %d %d of them." % fa)

        self.args['commands'].append("%d D %d %d %d" % fa)

        self._pos = order._pos


def run(args):

    start = time.time()

    args['commands'] = []

    args['gridsize'] = (args['cols'], args['rows'])
    #args['time_limit']
    args['product_T'] = args['product_types']
    args['nr_product_T'] = len(args['product_types'])
    #args['product_types']

    # Drone
    for idx, d in enumerate(args['drones']):
        gl_drones[idx] = Drone(args, idx, d['coords'], args['max_payload'])

    # Warehouses
    for idx, d in enumerate(args['warehouses']):
        gl_warehouses[idx] = Warehouse(args, idx, d['coords'], d['products'])

    # Orders
    for idx, d in enumerate(args['orders']):
        gl_orders[idx] = Order(args, idx, d['coords'], d['products'])

    print("### Loop ###")

    loop(args)

    print("### Loop end ###")

    # Save to file
    solutionf = open("solution.txt", 'w')

    print("%d" % len(args['commands']), file=solutionf)

    for cmd in args['commands']:
        print(cmd, file=solutionf)

    duration = time.time() - start
        
    log.info("Simulation took %.2fs." % duration)


def loop(args):

    while True:

        # gather all free drones
        free = [d for d in gl_drones.values() if not d.busy]

        # Go through all non served orders
        non_served = [tmp for tmp in gl_orders.values() if not tmp.served]

        c = Counter()
        for order in non_served:

            if sum([1 for _, w in gl_warehouses.items() if w.can_fulfil(order)['not_available'] == 0]) > 0:
                c['match'] += 1

            c['counter'] += 1

        print("%d/%d orders can be fulfilled by only one warehouse trip." % (c['match'], c['counter']))

        #order, drone, warehouses = next_order(free, non_served)

        return


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


if __name__ == "__main__":

    sim = load('busy_day.in')

    run(sim)
