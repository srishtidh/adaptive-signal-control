from __future__ import print_function
from __future__ import division

import json
import xml.etree.ElementTree as ET


class Artery(object):

    def __init__(self, edges):
        self.edges = edges
    
    def is_traversed(self, route):
        for edge in self.edges:
            if edge in route:
                return True
        return False


def get_arterial_vehicles(routefile, artery):
    tree = ET.parse(routefile)
    root = tree.getroot()

    arterial_vehicles = []

    for vehicle in root:
        if vehicle.tag != 'vehicle':
            continue
        [route] = list(vehicle)
        if artery.is_traversed(route.get('edges')):
            arterial_vehicles.append(vehicle.get('id'))

    return arterial_vehicles


def main():
    artery = Artery(['left0to0/0', '0/0to1/0', '1/0to2/0', '2/0to3/0', '3/0to4/0'])

    with open('files.json') as fp:
        routefiles = json.load(fp)

    for label, routefile in routefiles.items():
        vehicles = get_arterial_vehicles(routefile, artery)

        with open('{}-arterial.json'.format(label), 'w') as fp:
            json.dump(vehicles, fp, indent=4, sort_keys=True)

if __name__ == '__main__':
    main()
