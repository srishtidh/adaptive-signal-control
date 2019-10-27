from __future__ import print_function

import json
import argparse

import sumolib


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--info-file', required=True, help='TLS info file')
    parser.add_argument('--output', required=True, help='Output turns XML')
    args = parser.parse_args()
    return args


def nest_and_tweak(turn_ratios):
    grouped_turns = {}

    for turn in turn_ratios:
        in_edge = turn['incoming_edge']
        out_edge = turn['outgoing_edge']
        phase = turn['phase']
        ratio = turn['probability']

	# 60-10-30
        if ratio == 0.2:
            if phase in [2, 6]:
                ratio += 0.1
            else:
                ratio -= 0.1

        if in_edge not in grouped_turns:
            grouped_turns[in_edge] = {}
        # No need to store phase
        grouped_turns[in_edge][out_edge] = ratio * 100

    return grouped_turns


def add_to_xml(turns, interval):
    for in_edge, out_edges in turns.items():
        in_edge_element = interval.addChild('fromEdge', {'id': in_edge})
        for out_edge, ratio in out_edges.items():
            in_edge_element.addChild('toEdge', {'id': out_edge,
                                                'probability': ratio})


def main():
    args = get_args()

    with open(args.info_file, 'r') as fp:
        tls_info = json.load(fp)

    turn_xml = sumolib.xml.create_document('turns')

    interval_element = turn_xml.addChild('interval')
    interval_element.setAttribute('begin', '0')
    interval_element.setAttribute('end', '10000')
   
    for tls, info in tls_info.items():
        raw_turn_ratios = info['turn_proportions']
        turn_ratios = nest_and_tweak(raw_turn_ratios)
        add_to_xml(turn_ratios, interval_element)

    with open(args.output, 'w') as fp:
        fp.write(turn_xml.toXML())


if __name__ == '__main__':
    main()
