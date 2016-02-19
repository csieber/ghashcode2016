# -*- coding: utf-8 -*-

import time
import logging
import numpy as np
from load import load
from collections import Counter

log = logging.getLogger(__name__)

def distance(f, t):
    return int(np.round(np.sqrt(np.power(np.abs(f.pos[0] - t.pos[0]), 2) + np.power(np.abs(f.pos[1] - t.pos[1]), 2))))

gl_warehouses = {}
gl_drones = {}
gl_products = {}
gl_orders = {}


class Warehouse(object):

    def __init__(self, args, id, pos, products):

        self.args = args
        self.id = id

        self.pos = pos

        self._stock = {}

        for i in range(args['nr_product_T']):
            self._stock[i] = products[i]

    def take(self, p_T, count):

        print("Warehouse %d: Taking %d of product %d." % (self.id, p_T, count))

        assert(self._stock[p_T] >= count)

        self._stock[p_T] -= count

    def can_fulfil(self, order):

        count = Counter()

        for p_T, c in order._products.items():

            if self._stock[p_T] < c:
                count['not_available'] += 1
            else:
                count['available'] += 1

            count['count'] += 1

        #print("Warehouse %d, Order %d: %d/%d products available" % (self.id, order._id, count['available'], count['count']))

        return count

    def stock(self, p_T):
        return self._stock[p_T]


class Order(object):

    def __init__(self, args, id, to, products):
        self._id = id
        self.pos = to
        self.args = args

        self._products = {}

        for i in range(args['nr_product_T']):
            s = sum([1 for p in products if p == i])

            if s > 0:
                self._products[i] = s

        self.served = False

    def weight(self):
        return sum([v * self.args['product_T'][k] for k, v in self._products.items()])


class Drone(object):

    def __init__(self, args, id, pos, capacity):
        self.args = args
        self._id = id
        self._capacity = capacity

        self._current_load = 0

        self._load = Counter()

        self.pos = pos

        self.free_at = 0

    def free(self, time):
        if self.free_at <= time:
            return True
        else:
            return False

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

        print("Drone %d: Unloading %d times product %d" % (self._id, count, p_T))
        assert(count > 0)

        self._load[p_T] -= count

        self._current_load -= self.args['product_T'][p_T] * count

        assert(self._current_load >= 0)

    def serve(self, order, warehouses):

        order.served = True

        takes_t = 0

        for w in warehouses:

            takes = {}

            for p_T, count in order._products.items():

                print("Order %d: We need %d times %d" % (order._id, count, p_T))

                print("Counters: Warehouse (%d) / Order (%d) / space left (%d)" % (w.stock(p_T), count, self.space(p_T)))
                takes[p_T] = min(w.stock(p_T), count, self.space(p_T))

                takes_t += self.load(w, p_T, takes[p_T])

            for p_T, count in takes.items():
                takes_t += self.deliver(order, p_T, count)

        return takes_t

    def serve_multiple_trips(self, order, warehouses):

        order.served = True

        takes_t = 0

        for w in warehouses:

            while sum([count for _, count in order._products.items()]) > 0:

                takes = {}

                for p_T, count in order._products.items():

                    print("Order %d: We need %d times %d" % (order._id, count, p_T))

                    print("Counters: Warehouse (%d) / Order (%d) / space left (%d)" % (w.stock(p_T), count, self.space(p_T)))

                    c = min(w.stock(p_T), count, self.space(p_T))

                    if c == 0:
                        continue

                    takes[p_T] = c

                    takes_t += self.load(w, p_T, takes[p_T])

                for p_T, count in takes.items():
                    takes_t += self.deliver(order, p_T, count)

        return takes_t


    def load(self, warehouse, p_T, count):

        warehouse._stock[p_T] -= count

        self.put(p_T, count)

        self.args['commands'].append("%d L %d %d %d" % (self._id, warehouse.id, p_T, count))

        takes_t = distance(warehouse, self)

        self.pos = warehouse.pos

        return takes_t + 1


    def unload(self, warehouse, p_T, count):

        print("Drone %d unloading at warehouse %d product type %d %d times." % (self._id, warehouse.id, p_T, count))

        self.args['commands'].append("%d U %d %d %d" % (self._id, warehouse.id, p_T, count))

        self.pos = warehouse.pos

        return 1


    def deliver(self, order, p_T, count):

        order._products[p_T] -= count
        self.pull(p_T, count)

        fa = (self._id, order._id, p_T, count)
        print("Drone %d delivering for order %d product type %d %d of them." % fa)

        self.args['commands'].append("%d D %d %d %d" % fa)

        takes_t = distance(order, self)

        self.pos = order.pos

        return takes_t + 1


def run(args):

    global gl_warehouses, gl_drones, gl_products, gl_orders

    gl_warehouses = {}
    gl_drones = {}
    gl_products = {}
    gl_orders = {}

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

    order_c, score = loop(args)

    print("### Loop end (%d orders served, score %d)###" % (order_c, score))

    # Save to file
    solutionf = open("solution_%s.txt" % args['scenario'], 'w')

    print("%d" % len(args['commands']), file=solutionf)

    for cmd in args['commands']:
        print(cmd, file=solutionf)

    duration = time.time() - start
        
    log.info("Simulation took %.2fs." % duration)

    return score


def loop(args):

    easy_orders = []

    for order in gl_orders.values():
        if order.weight() <= args['max_payload']:
            for w in gl_warehouses.values():
                if w.can_fulfil(order)['not_available'] == 0:
                    easy_orders.append(order)
                    break

    print("Number of easy orders: %d" % len(easy_orders))

    score = 0
    orders_c = 0

    for NOW in range(args['time_limit']):

        # gather all free drones
        free = [d for d in gl_drones.values() if d.free(NOW)]

        # Go through all non served orders
        non_served = [tmp for tmp in gl_orders.values() if not tmp.served]

        c = Counter()

        for order in non_served:

            tmp = [1 for _, w in gl_warehouses.items() if w.can_fulfil(order)['not_available'] == 0]

            if len(tmp) > 0:

                c['at_stock_at_single_w'] += 1

                if order.weight() <= args['max_payload']:
                    c['order_fits_payload'] += 1

            c['counter'] += 1

        print("%d/%d orders can be fulfilled by only one warehouse trip." % (c['at_stock_at_single_w'], c['counter']))
        print("%d of those orders can be completed by one drone trip." % c['order_fits_payload'])

        print("%d: %d/%d drones free right now." % (NOW, len(free), len(gl_drones)))

        while len(free) > 0 and len(easy_orders) > 0:

            drone = free.pop()
            order = easy_orders.pop()

            for _, w in gl_warehouses.items():
                if w.can_fulfil(order)['not_available'] == 0:
                    takes_t = drone.serve(order, [w])
                    drone.free_at = NOW + takes_t
                    score += np.ceil((args['time_limit'] - drone.free_at)/args['time_limit']*100)
                    orders_c += 1
                    break

        if len(easy_orders) == 0:
            break

    print("END GAME MODE!")

    easy_orders = []

    for order in [o for o in gl_orders.values() if not o.served]:
         for _, w in gl_warehouses.items():
             if w.can_fulfil(order)['not_available'] == 0:
                easy_orders.append(order)
                break

    for NOW in range(NOW, args['time_limit']):

        free = [d for d in gl_drones.values() if d.free(NOW)]

        while len(free) > 0 and len(easy_orders) > 0:

            drone = free.pop()
            order = easy_orders.pop()

            for _, w in gl_warehouses.items():
                if w.can_fulfil(order)['not_available'] == 0:
                    print("Multiple trips")
                    takes_t = drone.serve_multiple_trips(order, [w])
                    drone.free_at = NOW + takes_t
                    score += np.ceil((args['time_limit'] - drone.free_at)/args['time_limit']*100)
                    orders_c += 1
                    break

        if len(easy_orders) == 0:
            return orders_c, score


if __name__ == "__main__":

    scores = {}
    for i in ['redundancy.in', 'busy_day.in', 'mother_of_all_warehouses.in']:
        sim = load(i)
        scores[i] = run(sim)

    print("--------------------")
    print("Scores:")
    for i, score in scores.items():
        print("%s: %d" % (i, score))
    print("--------------------")
    print("Total score: %d" % sum(scores.values()))
