import json
import pickle
import argparse
import numpy as np
from collections import namedtuple


Turn = namedtuple('Turn', ['in_edge', 'outflows', 'probabilities'])
Outflow = namedtuple('Outflow', ['out_edge', 'phase'])


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--turns-file', required=True, help='Turns file (.pkl)')
    parser.add_argument('--flow-file', required=True, help='Flow file (.json)')
    parser.add_argument('--output-file', required=True, help='Output file')
    parser.add_argument('--sample-count', type=int, required=True, help='Sample count')
    args = parser.parse_args()
    return args


def sample_outflows_for_edge(edge, turns, sample_count):
    outflow_count = len(turns.outflows)
    indices = np.random.choice(outflow_count,
                               size=sample_count,
                               p=turns.probabilities)
    return [turns.outflows[index] for index in indices]

# Warning: Works only for a single intersection!
def main():
    args = get_args()

    with open(args.turns_file) as fp:
        turns = pickle.load(fp)

    with open(args.flow_file) as fp:
        flows = json.load(fp)

    samples = {}

    for flow in flows:
        
        route = flow['route'].split()
        count = flow['count']
        prefix = flow['id']

        for vehIndex in range(count):
            vehID = '{}.{}'.format(prefix, vehIndex)
            samples[vehID] = {}

            processed_edges = set()
            unprocessed_edges = set()

            for edge in route:
                if edge in unprocessed_edges:
                    raise ValueError('{} occurs twice in {}\'s route'.format(edge, vehID))
                unprocessed_edges.add(edge)

            while unprocessed_edges:

                edge = unprocessed_edges.pop()
                
                # Don't sample on boundary edges
                if edge not in turns:
                    continue

                if edge in processed_edges:
                    continue

                sampled_outflows = sample_outflows_for_edge(edge, turns[edge], args.sample_count)
                samples[vehID][edge] = sampled_outflows
                processed_edges.add(edge)
                
                for (out_edge, phase) in sampled_outflows:
                    if out_edge not in processed_edges:
                        unprocessed_edges.add(out_edge)
            
    with open(args.output_file, 'w') as fp:
        pickle.dump(samples, fp)


if __name__ == '__main__':
    main()
