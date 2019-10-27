from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from collections import namedtuple
from copy import deepcopy
import pickle
import argparse


Turn = namedtuple('Turn', ['in_edge', 'outflows', 'probabilities'])
Outflow = namedtuple('Outflow', ['out_edge', 'phase'])


class Flow(object):
    def __init__(self, route, count, begin, end):
        self.route = route
        self.count = count
        self.begin = begin
        self.end = end


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demand', required=True, help='Demand label')
    args = parser.parse_args()
    return args


def get_possible_flows(flows, turns):

    partial_routes = flows
    full_routes = []

    while partial_routes:
        flow = partial_routes.pop(0)
        last_edge = flow.route[-1]
        if last_edge not in turns:
            full_routes.append(flow)
        else:
            next_turn = turns[last_edge]
            for outflow, probability in zip(next_turn.outflows, next_turn.probabilities):
                new_vehicle_count = flow.count * probability
                new_route = deepcopy(flow.route)
                new_route.append(outflow.out_edge)
                partial_routes.insert(0, Flow(route=new_route, count=new_vehicle_count,
                                              begin=flow.begin, end=flow.end))       

    return full_routes


def create_flow_xml(flows):
    root = Element('routes')

    vType = SubElement(root, 'vType', {'id': 'car',
                                       'speedDev': str(0.1),
                                       'guiShape': 'passenger',
                                       'color': '1,1,0'})

    for flow_id, flow in enumerate(flows):
        first_edge = flow.route.pop(0)
        last_edge = flow.route.pop(-1)
        attributes = {'id': str(flow_id),
                      'begin': str(flow.begin),
                      'end': str(flow.end),
                      'number': str(int(round(flow.count))),
                      'type': 'car',
                      'from': first_edge,
                      'to': last_edge}
        intermediate_edges = flow.route
        if intermediate_edges:
            attributes['via'] = ' '.join(intermediate_edges)
        flow = SubElement(root, 'flow', attributes)

    raw_string = tostring(root, 'utf-8')
    reparsed_string = minidom.parseString(raw_string)
    flow_xml = reparsed_string.toprettyxml(indent='    ')

    return flow_xml


# TODO: Allow demand profile to be input from a file
def main():
    args = get_args()

    flows = [
             Flow(route=["-gneE3"], count=105, begin=0, end=600),
             Flow(route=["gneE0"], count=45, begin=0, end=600),
             Flow(route=["-gneE3"], count=75, begin=600, end=1200),
             Flow(route=["gneE0"], count=75, begin=600, end=1200),
             Flow(route=["-gneE3"], count=45, begin=1200, end=1800),
             Flow(route=["gneE0"], count=105, begin=1200, end=1800),
            ]
    
    turn_files = [
                  '/home/srishti/adasco/experiments/ICAPS-2019/1x1/config/isolated.turn.pkl'
                 ]

    flow_files = [
                  '/home/srishti/adasco/experiments/ICAPS-2019/1x1/config/{0}/{0}.flow.xml'.format(args.demand)
                 ]
    
    for turn_file, flow_file in zip(turn_files, flow_files):
        with open(turn_file) as fp:
            turns = pickle.load(fp)
        flow_xml = create_flow_xml(get_possible_flows(flows, turns))
        with open(flow_file, 'w') as fp:
            fp.write(flow_xml)


if __name__ == '__main__':
    main()