from __future__ import division

import json
import argparse

import numpy as np

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--occ', required=True,
                        help='Occupancy file (as JSON file)')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    with open(args.occ) as fp:
    	occupancy = json.load(fp)

    means = []
    maxs = []
    mins = []
    
    for e, o in occupancy.items():
        c = [n*100/0.66 for n in o]
        means.append(np.mean(c))
        maxs.append(max(c))
        mins.append(min(c))

    print('Means: {}'.format(means))
    print('Maxs: {}'.format(maxs))
    print('Mins: {}'.format(mins))
