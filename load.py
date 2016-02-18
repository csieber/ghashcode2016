__author__ = 'Mikhail Vilgelm'
# import pprint


def load(filename):

    simulation = {}

    f = open('in/'+filename)
    lines = f.readlines()
    f.close()

    i = 0
    while True:
        if i==0:
            line_data = lines[i].split(' ')
            simulation['rows'] = int(line_data[0])
            simulation['cols'] = int(line_data[1])
            simulation['drones'] = [{'coords': (float('nan'),float('nan')), 'load': 0}]*int(line_data[2])
            simulation['time_limit'] = int(line_data[3])
            simulation['max_payload'] = int(line_data[4])
            i+=1
            continue

        if i==1:
            simulation['product_types'] = [None]*int(lines[i])
            i+=1
            continue

        if i==2:
            simulation['product_types'] = list(map(int, lines[i].split(' ')))
            i+=1
            continue

        if i==3:
            simulation['warehouses'] = [None]*int(lines[i])
            i+=1
            continue

        if i==4:
            # read in every warehouse
            for j in range(len(simulation['warehouses'])):
                # read warehouse data
                wh = {'coords': tuple(map(int, lines[i].split(' ')))}
                wh['products'] = list(map(int, lines[i+1].split(' ')))
                # print(wh)
                simulation['warehouses'][j] = wh
                i+=2
            continue

        else:
            # read in every order
            simulation['orders'] = []
            number_of_orders = int(lines[i])
            i+=1
            for j in range(number_of_orders):
                # for every order
                order = {'coords': (tuple(map(int, lines[i].split(' '))))}
                order['products'] = list(map(int, lines[i+2].split(' ')))
                simulation['orders'].append(order)
                i+=3
            break

    for drone in simulation['drones']:
        drone['coords'] = simulation['warehouses'][0]['coords']
        drone['load'] = simulation['max_payload']

    simulation['scenario'] = filename

    return simulation



if __name__=='__main__':

    sim = load('busy_day.in')

    print(sim['drones'])
    print(len(sim['drones']))

    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(sim['warehouses'])
    print(sim['warehouses'])
    print(sim['orders'])
    print(sim['drones'])
