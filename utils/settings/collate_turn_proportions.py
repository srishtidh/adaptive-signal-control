import json
import pickle
import argparse
import xml.etree.ElementTree as ET
from collections import namedtuple


Turn = namedtuple('Turn', ['in_edge', 'outflows', 'probabilities'])
Outflow = namedtuple('Outflow', ['out_edge', 'phase'])


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--info-file', required=True,
                        help='TLS info file')
    parser.add_argument('--output-file', required=True,
                        help='Output file')
    args = parser.parse_args()
    return args


def parse_and_collate_turns(info_file):
    with open(info_file, 'r') as fp:
        settings = json.load(fp)

    turns = {}

    for tls, setting in settings.items():
        for turn in setting['turn_proportions']:
            in_edge = turn['incoming_edge']
            out_edge = turn['outgoing_edge']
            phase = turn['phase']
            probability = turn['probability']

            if in_edge not in turns:
                turns[in_edge] = Turn(in_edge=in_edge,
                                      outflows=[],
                                      probabilities=[])
        
            turns[in_edge].outflows.append(Outflow(out_edge=out_edge,
                                                   phase=phase))
            turns[in_edge].probabilities.append(probability)

    return turns


def main():
    args = get_args()
    
    turns = parse_and_collate_turns(args.info_file)
    
    with open(args.output_file, 'w') as fp:
        pickle.dump(turns, fp)

    print('Turns pickled to {}'.format(args.output_file))


if __name__ == '__main__':
    main()