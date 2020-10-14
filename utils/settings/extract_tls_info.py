from __future__ import print_function
from __future__ import division

import re
import os
import imp
import json
import argparse
import xml.etree.ElementTree as ET

import sumolib # Why not TraCI?

FILE_DIR, FILE = os.path.split(os.path.realpath(__file__))
DEFAULT_PARAMS = os.path.join(FILE_DIR, 'params.py')    


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--net-file', required=True,
                        help='SUMO net file')
    parser.add_argument('-t', '--turns-file', required=True,
                        help='Turns file')
    parser.add_argument('-o', '--output-file', required=True,
                        help='Output file')
    parser.add_argument('-p', '--params-file', default=DEFAULT_PARAMS,
                        help='Params file, default: {}'.format(DEFAULT_PARAMS))
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    net_file = args.net_file
    turns_file = args.turns_file
    output_file = args.output_file

    net = sumolib.net.readNet(net_file, withPrograms=True)
    lights = net.getTrafficLights()

    info = {tls.getID():{} for tls in lights}
    order = 1

    params = imp.load_source('params', args.params_file)

    read_turn_proportions(info, turns_file, net)

    for tls in lights:

        tlsID = tls.getID()
        #print(str(info))
        info[tlsID]['id'] = tlsID
        info[tlsID]['phases'] = []
        info[tlsID]['Y'] = {}
        info[tlsID]['Gmin'] = {}
        info[tlsID]['Gmax'] = {}
        info[tlsID]['incoming_edges'] = {}
        info[tlsID]['outgoing_edges'] = {}
        info[tlsID]['upstream_agents'] = []
        info[tlsID]['edge_lengths'] = {}
        info[tlsID]['order'] = order
        order += 1

        info[tlsID]['free_flow_speed'] = params.free_flow_speed
        info[tlsID]['headway'] = params.headway
        info[tlsID]['saturation_flow_rate'] = params.saturation_flow_rate
        info[tlsID]['startup_lost_time'] = params.startup_lost_time
        
        info[tlsID]['time_resolution'] = params.time_resolution
        info[tlsID]['sampling_interval'] = params.sampling_interval
        info[tlsID]['horizon_extension'] = params.horizon_extension
        info[tlsID]['merging_threshold'] = params.merging_threshold
        info[tlsID]['extension_threshold'] = params.extension_threshold
        info[tlsID]['minimum_extension'] = params.minimum_extension

        programs = tls.getPrograms()
        if len(programs) != 1:
            raise ValueError('{} does not have a single program'.format(tlsID))
        
        main_program = programs.values().pop()
        phases = main_program.getPhases()

        for index, (definition, duration) in enumerate(phases):
            if is_green_phase(definition):
                info[tlsID]['phases'].append(index)
                info[tlsID]['Gmin'][index] = params.Gmin
                info[tlsID]['Gmax'][index] = params.Gmax
                info[tlsID]['Y'][index] = params.Y

        links = tls.getConnections()
        
        for [in_lane, out_lane, link_index] in links:
            
            in_lane_id = in_lane.getID()
            in_edge = in_lane.getEdge()
            in_edge_id = in_edge.getID()
            out_lane_id = out_lane.getID()
            out_edge = out_lane.getEdge()
            out_edge_id = out_edge.getID()
            
            # Add incoming edges
            if in_edge_id not in info[tlsID]['incoming_edges']:
                info[tlsID]['incoming_edges'][in_edge_id] = []
            if in_lane_id not in info[tlsID]['incoming_edges'][in_edge_id]:
                info[tlsID]['incoming_edges'][in_edge_id].append(in_lane_id)

            # Add outgoing edges
            if out_edge_id not in info[tlsID]['outgoing_edges']:
                info[tlsID]['outgoing_edges'][out_edge_id] = []
            if out_lane_id not in info[tlsID]['outgoing_edges'][out_edge_id]:
                info[tlsID]['outgoing_edges'][out_edge_id].append(out_lane_id)

            # Add phases to turn proportions
            for phase_index, (definition, duration) in enumerate(phases):
                if right_of_way(definition, link_index):
                    turns = [turn for turn in info[tlsID]['turn_proportions']
                             if turn['incoming_edge'] == in_edge_id
                             and turn['outgoing_edge'] == out_edge_id]
                    # Why would it not exist?
                    if turns:
                        turn = turns[0]
                        turn['phase'] = phase_index

        # Add upstream agents
        for in_edge in tls.getEdges():
            # Problem: Node and TL IDs may differ (spider case)
            # Workaround: Rename tlLogic elements to match corresponding nodes
            # Works for now; make sure TLS and corresponding nodes are of same name
            in_edge_id = in_edge.getID()
            from_node = in_edge.getFromNode()
            if is_traffic_light(from_node):
                info[tlsID]['upstream_agents'].append({'id': from_node.getID(),
                                                       'connecting_edge': in_edge_id})

            # Add edge_lengths
            length = in_edge.getLength()
            info[tlsID]['edge_lengths'][in_edge_id] = length

    with open(output_file, 'w') as fp:
        json.dump(info, fp, indent=4, sort_keys=True)


def read_turn_proportions(info, turns_file, net):
    tree = ET.parse(turns_file)
    root = tree.getroot()
    #interval_element = root.getchildren()[0]
    interval_element = root.getchildren()

    for from_edge_element in interval_element:
        
        from_edge_id = from_edge_element.get('id')
        from_edge = net.getEdge(from_edge_id)
        to_tls = from_edge.getTLS()

        if to_tls:
            tlsID = to_tls.getID()    
            for to_edge_element in from_edge_element:
                to_edge_id = to_edge_element.get('id')
                probability = float(to_edge_element.get('probability')) / 100
                turn = {}
                turn['incoming_edge'] = from_edge_id
                turn['outgoing_edge'] = to_edge_id
                turn['probability'] = probability
                try:
                    info[tlsID]['turn_proportions'].append(turn)
                except KeyError:
                    info[tlsID]['turn_proportions'] = [turn]


def is_traffic_light(node):
    return (node.getType() == 'traffic_light')


def is_green_phase(definition):
    return ('G' in definition)


def right_of_way(definition, link_index):
    return (definition[link_index] == 'G')

if __name__ == '__main__':
    main()
