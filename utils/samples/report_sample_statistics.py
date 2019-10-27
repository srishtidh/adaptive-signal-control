from __future__ import print_function
from collections import namedtuple
import pickle
import argparse
import pprint

import numpy as np


Turn = namedtuple('Turn', ['in_edge', 'outflows', 'probabilities'])
Outflow = namedtuple('Outflow', ['out_edge', 'phase'])


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--turns',
                        help='Pickled turns for the network')
    parser.add_argument('--samples',
                        help='Pickled sample set')
    parser.add_argument('--count', type=int,
                        help='Number of realizations to consider')
    args = parser.parse_args()
    return args


def distance(dictA, dictB):
    vectorA = []
    vectorB = []

    for key in dictA:
        vectorA.append(dictA[key])
        vectorB.append(dictB[key])

    return np.linalg.norm(np.array(vectorA)-np.array(vectorB))


def main():
    args = get_args()

    with open(args.turns) as fp:
        turns = pickle.load(fp)

    with open(args.samples) as fp:
        sample_set = pickle.load(fp)

    samples = [{} for sample in range(args.count)]
    mean = {}
    expectation = {}

    for vehicle, route in sample_set.items():
        for edge, outflows in route.items():
            for sample_id, outflow in enumerate(outflows[:args.count]):
                sample = samples[sample_id]
                sample[(vehicle, outflow)] = 1
                for outflow, probability in zip(turns[edge].outflows, turns[edge].probabilities):
                    if (vehicle, outflow) not in sample:
                        sample[(vehicle, outflow)] = 0

                if sample_id == 0:
                    for outflow, probability in zip(turns[edge].outflows, turns[edge].probabilities):
                        expectation[(vehicle, outflow)] = probability
        
        # print('Expectation')        
        # pprint.pprint(expectation)
        # print()
        # print('Samples')
        # pprint.pprint(samples)
        # print()
        # print('===================================================================')
        # print()
 

    for key in expectation:
        mean[key] = np.mean([sample[key] for sample in samples])

    dist_from_exp = distance(mean, expectation)
    variance = np.mean([np.square(distance(sample, mean)) for sample in samples])

    # for sample in samples:
    #     print('Dist from mean = {}'.format(distance(sample, mean)))
    
    # pprint.pprint(mean)
    print('Distance from exp = {}'.format(dist_from_exp))
    print('Variance = {}'.format(variance))


if __name__ == '__main__':
    main()
                
                
