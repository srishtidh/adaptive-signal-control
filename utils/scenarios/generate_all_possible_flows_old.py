from __future__ import print_function

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from collections import namedtuple
from copy import deepcopy
import pickle
import argparse

import numpy as np


Turn = namedtuple('Turn', ['in_edge', 'outflows', 'probabilities'])
Outflow = namedtuple('Outflow', ['out_edge', 'phase'])


class Flow(object):
    def __init__(self, route, count, begin, end):
        self.route = route
        self.count = count
        self.begin = begin
        self.end = end

    def __repr__(self):
        return 'Flow(route={}, count={})'.format(self.route, self.count)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--turn-file', required=True, help='Turn file (.pkl)')
    parser.add_argument('--output-file', required=True, help='Output file (.flow.xml)')
    args = parser.parse_args()
    return args


def get_possible_flows(flows, turns):

    partial_routes = flows
    full_routes = []

    while partial_routes:
        flow = partial_routes.pop(0)
        # print()
        # print(flow)
        divisible = True
        last_edge = flow.route[-1]
        if last_edge not in turns:
            full_routes.append(flow)
        else:
            next_turns = turns[last_edge]
            
            next_counts = [flow.count * probability for probability in next_turns.probabilities]
            # print(next_counts)
            fractional_counts = [count for count in next_counts if count < 1]
            if fractional_counts:
              divisible = False

            if divisible:
              for outflow, probability in zip(next_turns.outflows, next_turns.probabilities):
                  new_vehicle_count = flow.count * probability
                  # print('New vehicle count = {} * {} = {}'.format(flow.count, probability, new_vehicle_count))
                  new_route = deepcopy(flow.route)
                  new_route.append(outflow.out_edge)
                  partial_routes.insert(0, Flow(route=new_route, count=new_vehicle_count,
                                                begin=flow.begin, end=flow.end))
            else:
              # Sample next turn
              sampled_index = np.random.choice(len(next_turns.outflows),
                                               p=next_turns.probabilities)
              sampled_outflow = next_turns.outflows[sampled_index]
              new_vehicle_count = flow.count
              # print('New vehicle count = {}'.format(new_vehicle_count))
              new_route = deepcopy(flow.route)
              new_route.append(sampled_outflow.out_edge)
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


def main():
    args = get_args()

    #from flows import flows
    """
    flows = [Flow(route=["-11694197#0"], count=90, begin=0, end=300),
         Flow(route=["625851637"], count=90, begin=0, end=300),
         Flow(route=["322361922#0"], count=90, begin=0, end=300),
         Flow(route=["-320948884#0"], count=45, begin=0, end=300),
         Flow(route=["-54460235#4"], count=45, begin=0, end=300),
         Flow(route=["54500409#4"], count=45, begin=0, end=300),
         Flow(route=["-25626142"], count=45, begin=0, end=300), #77

         Flow(route=["-11694197#0"], count=56, begin=300, end=600),
         Flow(route=["625851637"], count=56, begin=300, end=600),
         Flow(route=["322361922#0"], count=56, begin=300, end=600),
         Flow(route=["-320948884#0"], count=64, begin=300, end=600),
         Flow(route=["-54460235#4"], count=64, begin=300, end=600),
         Flow(route=["54500409#4"], count=40, begin=300, end=600),
         Flow(route=["-25626142"], count=64, begin=300, end=600),

         Flow(route=["-11694197#0"], count=45, begin=600, end=900),
         Flow(route=["625851637"], count=45, begin=600, end=900),
         Flow(route=["322361922#0"], count=45, begin=600, end=900),
         Flow(route=["-320948884#0"], count=90, begin=600, end=900),
         Flow(route=["-54460235#4"], count=90, begin=600, end=900),
         Flow(route=["54500409#4"], count=45, begin=600, end=900),
         Flow(route=["-25626142"], count=90, begin=600, end=900),]"""
         
    flows = [Flow(route=["-11694197#0"], count=160, begin=0, end=300),
         Flow(route=["625851637"], count=160, begin=0, end=300),
         Flow(route=["322361922#0"], count=160, begin=0, end=300),
         Flow(route=["-320948884#0"], count=80, begin=0, end=300),
         Flow(route=["-54460235#4"], count=80, begin=0, end=300),
         Flow(route=["54500409#4"], count=80, begin=0, end=300),
         Flow(route=["-25626142"], count=80, begin=0, end=300), #77

         Flow(route=["-11694197#0"], count=112, begin=300, end=600),
         Flow(route=["625851637"], count=112, begin=300, end=600),
         Flow(route=["322361922#0"], count=112, begin=300, end=600),
         Flow(route=["-320948884#0"], count=128, begin=300, end=600),
         Flow(route=["-54460235#4"], count=128, begin=300, end=600),
         Flow(route=["54500409#4"], count=80, begin=300, end=600),
         Flow(route=["-25626142"], count=128, begin=300, end=600),

         Flow(route=["-11694197#0"], count=80, begin=600, end=900),
         Flow(route=["625851637"], count=80, begin=600, end=900),
         Flow(route=["322361922#0"], count=80, begin=600, end=900),
         Flow(route=["-320948884#0"], count=160, begin=600, end=900),
         Flow(route=["-54460235#4"], count=160, begin=600, end=900),
         Flow(route=["54500409#4"], count=80, begin=600, end=900),
         Flow(route=["-25626142"], count=160, begin=600, end=900),]
         
    """
    flows = [Flow(route=["-11694197#0"], count=130, begin=0, end=300),
         Flow(route=["625851637"], count=130, begin=0, end=300),
         Flow(route=["322361922#0"], count=130, begin=0, end=300),
         Flow(route=["-320948884#0"], count=65, begin=0, end=300),
         Flow(route=["-54460235#4"], count=65, begin=0, end=300),
         Flow(route=["54500409#4"], count=65, begin=0, end=300),
         Flow(route=["-25626142"], count=65, begin=0, end=300), #77

         Flow(route=["-11694197#0"], count=91, begin=300, end=600),
         Flow(route=["625851637"], count=91, begin=300, end=600),
         Flow(route=["322361922#0"], count=91, begin=300, end=600),
         Flow(route=["-320948884#0"], count=104, begin=300, end=600),
         Flow(route=["-54460235#4"], count=104, begin=300, end=600),
         Flow(route=["54500409#4"], count=65, begin=300, end=600),
         Flow(route=["-25626142"], count=104, begin=300, end=600),

         Flow(route=["-11694197#0"], count=65, begin=600, end=900),
         Flow(route=["625851637"], count=65, begin=600, end=900),
         Flow(route=["322361922#0"], count=65, begin=600, end=900),
         Flow(route=["-320948884#0"], count=130, begin=600, end=900),
         Flow(route=["-54460235#4"], count=130, begin=600, end=900),
         Flow(route=["54500409#4"], count=65, begin=600, end=900),
         Flow(route=["-25626142"], count=130, begin=600, end=900),]"""
    with open(args.turn_file) as fp:
        turns = pickle.load(fp)
    flow_xml = create_flow_xml(get_possible_flows(flows, turns))
    with open(args.output_file, 'w') as fp:
        fp.write(flow_xml)


if __name__ == '__main__':
    main()
