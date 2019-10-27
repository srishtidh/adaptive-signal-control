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
    parser.add_argument('--labels', required=True,
                        help='List of labels (as JSON file)')
    parser.add_argument('-o', '--output-prefix', required=True,
                        help='Output prefix')
    args = parser.parse_args()
    return args


def perf_gain(base, hypothesis):
    return 100 * (hypothesis - base) / base


def _parse_delay(filename):
    delay = '-'
    with open(filename, 'r') as fp:
        for line in fp:
            if 'WaitingTime' in line:
                s = line.split(' ')
                delay = float(s[2])
    return delay


def parse_and_store_delay(file, gains, row):
    try:
        delay = _parse_delay(file)
    except IOError:
        delay = '-'

    gains.append(delay)
    row.append(delay)


def analyse_and_print_gains(gains, label, fp):
        print('\n=====================================================================', file=fp)
        print(label, file=fp)
        print('Mean: {}'.format(np.mean(gains)), file=fp)
        print('Median: {}'.format(np.median(gains)), file=fp)
        print('Standard Deviation: {}'.format(np.std(gains)), file=fp)
        win_count = len([gain for gain in gains if gain < 0])
        print('Number of cases in which hypothesis outperforms base: {} / {} ({}%)'.format(win_count, len(gains), 100*win_count/len(gains)), file=fp)


def main():
    args = get_args()
    
    with open(args.labels, 'r') as fp:
        labels = json.load(fp)

    table = [['#',
              'Label',
              'Fixed',
              'U-SURTRAC',
              'C-SURTRAC',
              'U-CP-S1-TL5',
              'C-CP-S1-TL5',
              'C-CP-S1-TL10',
              'C-CP-S1-TL20',
              'U-CP-S5-TL5',
              'C-CP-S5-TL5',
              'C-CP-S5-TL10',
              'C-CP-S5-TL20',
              'U-CP-S20-TL5',
              'C-CP-S20-TL5',
              'C-CP-S20-TL10',
              'C-CP-S20-TL20']]
    
    fixed = []
    
    usurtrac = []
    csurtrac = []

    ucpgains = {}
    ccpgains = {}

    for sample_dir in ['S1', 'S5', 'S20']:
        
        ucpgains[sample_dir] = {}
        ccpgains[sample_dir] = {}

        for tl_dir in ['TL-5']:
            ucpgains[sample_dir][tl_dir] = []

        for tl_dir in ['TL-5', 'TL-10', 'TL-20']:
            ccpgains[sample_dir][tl_dir] = []

    log_dir = '/home/srishti/adasco/experiments/R5C5/log/all-turns/8-may-2018/60-20-20/1500V'

    for index, label in enumerate(labels):

        row = [index + 1, label]

        parse_and_store_delay(os.path.join(log_dir, label + '.fixed.summary.log'),
                              fixed, row)

        parse_and_store_delay(os.path.join(log_dir, label + '-uncoordinated.heuristic.summary.log'),
                              usurtrac, row)

        parse_and_store_delay(os.path.join(log_dir, label + '-coordinated.heuristic.summary.log'),
                              csurtrac, row)
        
        for sample_dir in ['S1', 'S5', 'S20']:
            for tl_dir in ['TL-5']:
                parse_and_store_delay(os.path.join(log_dir,
                                                   sample_dir,
                                                   'no-min-ext',
                                                   tl_dir,
                                                   label + '-{}-R001-uncoordinated.cp.summary.log'.format(sample_dir)),
                                      ucpgains[sample_dir][tl_dir], row)

            for tl_dir in ['TL-5', 'TL-10', 'TL-20']:
                parse_and_store_delay(os.path.join(log_dir,
                                                   sample_dir,
                                                   'no-min-ext',
                                                   tl_dir,
                                                   label + '-{}-R001-coordinated.cp.summary.log'.format(sample_dir)),
                                      ccpgains[sample_dir][tl_dir], row)

        table.append(row)
                    
    with open('{}.{}.log'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        print(tabulate.tabulate(table, headers='firstrow', tablefmt='grid'),
              file=fp)

    with open('{}.{}.json'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        json.dump(table, fp, indent=4)

    plt.figure(figsize=(20,5))
    lines = plt.plot(range(1, len(fixed)+1), fixed, ':.',
                     range(1, len(usurtrac)+1), usurtrac, ':.',
                     range(1, len(csurtrac)+1), csurtrac, ':.',
                     range(1, len(ucpgains['S1']['TL-5'])+1), ucpgains['S1']['TL-5'], ':.',
                     range(1, len(ccpgains['S1']['TL-5'])+1), ccpgains['S1']['TL-5'], ':.',
                     range(1, len(ccpgains['S1']['TL-10'])+1), ccpgains['S1']['TL-10'], ':.',
                     range(1, len(ccpgains['S1']['TL-20'])+1), ccpgains['S1']['TL-20'], ':.',
                     range(1, len(ucpgains['S5']['TL-5'])+1), ucpgains['S5']['TL-5'], ':.',
                     range(1, len(ccpgains['S5']['TL-5'])+1), ccpgains['S5']['TL-5'], ':.',
                     range(1, len(ccpgains['S5']['TL-10'])+1), ccpgains['S5']['TL-10'], ':.',
                     range(1, len(ccpgains['S5']['TL-20'])+1), ccpgains['S5']['TL-20'], ':.',
                     range(1, len(ucpgains['S20']['TL-5'])+1), ucpgains['S20']['TL-5'], ':.',
                     range(1, len(ccpgains['S20']['TL-5'])+1), ccpgains['S20']['TL-5'], ':.',
                     range(1, len(ccpgains['S20']['TL-10'])+1), ccpgains['S20']['TL-10'], ':.',
                     range(1, len(ccpgains['S20']['TL-20'])+1), ccpgains['S20']['TL-20'], ':.',
                     alpha=0.7)
    plt.legend(lines, ['Fixed',
                      'U-SURTRAC',
                      'C-SURTRAC',
                      'U-CP-S1-TL5',
                      'C-CP-S1-TL5',
                      'C-CP-S1-TL10',
                      'C-CP-S1-TL20',
                      'U-CP-S5-TL5',
                      'C-CP-S5-TL5',
                      'C-CP-S5-TL10',
                      'C-CP-S5-TL20',
                      'U-CP-S20-TL5',
                      'C-CP-S20-TL5',
                      'C-CP-S20-TL10',
                      'C-CP-S20-TL20'])
    plt.ylabel('Average Delay (s)')
    plt.title('5x5 intersection')
    plt.savefig('{}.delays.{}.png'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')))

if __name__ == '__main__':
    main()