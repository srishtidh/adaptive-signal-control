from __future__ import print_function
from __future__ import division

import matplotlib.pyplot as plt
import os
import time
import json
import numpy as np
import tabulate
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log-dir', default='',
                        help='Path of experiment log directory')
    parser.add_argument('--labels', required=True,
                        help='List of labels (as JSON file)')
    parser.add_argument('-o', '--output-prefix', required=True,
                        help='Output prefix')
    args = parser.parse_args()
    return args


def perf_gain(base, hypothesis):
    return 100 * (hypothesis - base) / base


def main():
    args = get_args()
    
    log_dir = os.path.abspath(args.log_dir)
    
    with open(args.labels, 'r') as fp:
        labels = json.load(fp)

    table = [['#, SchIC, CoMA, Performance Gain']]
    
    case = []
    schIC = []
    coma = []
    
    count = 1

    for label in labels:

        surtrac_summary = os.path.join(log_dir, label + '-uncoordinated.surtrac.summary.log')
        with open(surtrac_summary, 'r') as fp:
            for line in fp:
                if 'WaitingTime' in line:
                    s = line.split(' ')
                    surtrac_delay = float(s[2])
                    schIC.append(surtrac_delay)

        heuristic_summary = os.path.join(log_dir, label + '-coordinated.heuristic.summary.log')
        with open(heuristic_summary, 'r') as fp:
            for line in fp:
                if 'WaitingTime' in line:
                    s = line.split(' ')
                    coma_delay = float(s[2])
                    coma.append(coma_delay)
                    gain = perf_gain(surtrac_delay, coma_delay)

        table.append([count, surtrac_delay, coma_delay, gain])
                    
        case.append(count)
        count += 1

    with open('{}.{}.log'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        print(tabulate.tabulate(table, headers='firstrow', tablefmt='grid'),
              file=fp)
        
    with open('{}.{}.json'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        json.dump(table, fp, indent=4)

    plt.figure()
    lines = plt.plot(case, schIC, 'r--.', case, coma, 'b--.', alpha=0.7)
    plt.legend(lines, ['SchIC', 'CoMA'])
    plt.xlabel('Test Case')
    plt.ylabel('Average Delay')
    plt.title('SchIC vs CoMA')
    plt.savefig('{}.{}.png'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')))

if __name__ == '__main__':
    main()