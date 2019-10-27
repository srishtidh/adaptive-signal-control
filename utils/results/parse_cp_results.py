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
    parser.add_argument('-n', '--net', required=True,
                        help='Network name')
    parser.add_argument('--coordinate', default=False,
                        help='Include results for coordinated strategies')
    args = parser.parse_args()
    return args


def perf_gain(base, hypothesis):
    if (base == '-') or (hypothesis == '-'):
        return '-'
    return 100 * (hypothesis - base) / base


def parse_delay(filename):
    delay = '-'
    with open(filename, 'r') as fp:
        for line in fp:
            if 'WaitingTime' in line:
                s = line.split(' ')
                delay = float(s[2])
                break
    return delay

def print_gain_stats(gains, fileobj, label):
    if gains:
        print('\n=====================================================================', file=fileobj)
        print(label, file=fileobj)
        print('Mean: {}'.format(np.mean(gains)), file=fileobj)
        print('Median: {}'.format(np.median(gains)), file=fileobj)
        print('Standard Deviation: {}'.format(np.std(gains)), file=fileobj)
        count = len(gains)
        win = len([gain for gain in gains if gain < 0])
        print('Number of cases in which hypothesis outperforms base: {} / {} ({}%)'.format(win, count, (100*win/count)), file=fileobj)


def main():
    args = get_args()
    
    log_dir = os.path.abspath(args.log_dir)
    
    with open(args.labels, 'r') as fp:
        labels = json.load(fp)

    table = [['#',
              'Label',
              'Fixed',
              'U-SURTRAC', 'vs Fixed',
              'C-SURTRAC', 'vs Fixed', 'vs U-SURTRAC',
              'CP (1 sample)', 'vs Fixed', 'vs U-SURTRAC', 'vs C-SURTRAC',
              'CP (5 samples)', 'vs Fixed', 'vs U-SURTRAC', 'vs C-SURTRAC']]
    
    case = []
    fixed = []
    usurtrac = []
    csurtrac = []
    cp1 = []
    cp5 = []

    count = 1
    cp1_count = 0
    cp5_count = 0
    
    usurtrac_vs_fixed = []
    csurtrac_vs_fixed = []
    csurtrac_vs_usurtrac = []
    cp1_vs_fixed = []
    cp1_vs_usurtrac = []
    cp1_vs_csurtrac = []
    cp5_vs_fixed = []
    cp5_vs_usurtrac = []
    cp5_vs_csurtrac = []

    for label in labels:

        print('Processing label {}'.format(label))

        row = [count, label]

        # Fixed
        fixed_summary = os.path.join(log_dir, label + '.fixed.summary.log')
        fixed_delay = parse_delay(fixed_summary)
        fixed.append(fixed_delay)
        row.append(fixed_delay)

        # U-SURTRAC
        usurtrac_summary = os.path.join(log_dir, label + '-uncoordinated.heuristic.summary.log')
        usurtrac_delay = parse_delay(usurtrac_summary)
        usurtrac.append(usurtrac_delay)
        row.append(usurtrac_delay)
        
        vs_fixed = perf_gain(fixed_delay, usurtrac_delay)
        row.append(vs_fixed)
        usurtrac_vs_fixed.append(vs_fixed)
        
        # C-SURTRAC
        if args.coordinate:
            csurtrac_summary = os.path.join(log_dir, label + '-coordinated.heuristic.summary.log')
            csurtrac_delay = parse_delay(csurtrac_summary)
            csurtrac.append(csurtrac_delay)
            
            vs_fixed = perf_gain(fixed_delay, csurtrac_delay)
            csurtrac_vs_fixed.append(vs_fixed)

            vs_usurtrac = perf_gain(usurtrac_delay, csurtrac_delay)
            csurtrac_vs_usurtrac.append(vs_usurtrac)
        else:
            csurtrac_delay = '-'
            vs_fixed = '-'
            vs_usurtrac = '-'

        row.append(csurtrac_delay)
        row.append(vs_fixed)
        row.append(vs_usurtrac)

        # CP 1
        try:
            cp1_summary = os.path.join(log_dir, label + '-S1-R001-uncoordinated.cp.summary.log')
            cp1_delay = parse_delay(cp1_summary)
            row.append(cp1_delay)
            
            if cp1_delay != '-':
                cp1.append(cp1_delay)
                vs_fixed = perf_gain(fixed_delay, cp1_delay)
                vs_usurtrac = perf_gain(usurtrac_delay, cp1_delay)
                vs_csurtrac = perf_gain(csurtrac_delay, cp1_delay)

                cp1_vs_fixed.append(vs_fixed)
                cp1_vs_fixed.append(vs_usurtrac)

                if args.coordinate:    
                    cp1_vs_fixed.append(vs_csurtrac)

                cp1_count += 1
            else:
                vs_fixed = '-'
                vs_usurtrac = '-'
                vs_csurtrac = '-'
        except IOError:
            vs_fixed = '-'
            vs_usurtrac = '-'
            vs_csurtrac = '-'

        row.append(vs_fixed)
        row.append(vs_usurtrac)
        row.append(vs_csurtrac)


        # CP 5
        try:
            cp5_summary = os.path.join(log_dir, label + '-S5-R001-uncoordinated.cp.summary.log')
            cp5_delay = parse_delay(cp5_summary)
            row.append(cp5_delay)
            
            if cp5_delay != '-':
                cp5.append(cp5_delay)
                vs_fixed = perf_gain(fixed_delay, cp5_delay)
                vs_usurtrac = perf_gain(usurtrac_delay, cp5_delay)
                vs_csurtrac = perf_gain(csurtrac_delay, cp5_delay)
                cp5_count += 1

                cp5_vs_fixed.append(vs_fixed)
                cp5_vs_fixed.append(vs_usurtrac)

                if args.coordinate:    
                    cp5_vs_fixed.append(vs_csurtrac)
            else:
                vs_fixed = '-'
                vs_usurtrac = '-'
                vs_csurtrac = '-'
        except IOError:
            vs_fixed = '-'
            vs_usurtrac = '-'
            vs_csurtrac = '-'
            
        row.append(vs_fixed)
        row.append(vs_usurtrac)
        row.append(vs_csurtrac)
        
        table.append(row)
                    
        case.append(count)
        count += 1

    with open('{}.{}.log'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        print(tabulate.tabulate(table, headers='firstrow', tablefmt='grid'),
              file=fp)

        print_gain_stats(usurtrac_vs_fixed, fp, 'U-SURTRAC vs Fixed')

        if args.coordinate:
            print_gain_stats(csurtrac_vs_fixed, fp, 'C-SURTRAC vs Fixed')
            print_gain_stats(csurtrac_vs_usurtrac, fp, 'C-SURTRAC vs U-SURTRAC')

        if cp1_count > 0:   
            print_gain_stats(cp1_vs_fixed, fp, 'CP (S1) vs Fixed')
            print_gain_stats(cp1_vs_usurtrac, fp, 'CP (S1) vs U-SURTRAC')
            if args.coordinate:
                print_gain_stats(cp1_vs_csurtrac, fp, 'CP (S1) vs C-SURTRAC')

        if cp5_count > 0:   
            print_gain_stats(cp5_vs_fixed, fp, 'CP (S5) vs Fixed')
            print_gain_stats(cp5_vs_usurtrac, fp, 'CP (S5) vs U-SURTRAC')
            if args.coordinate:
                print_gain_stats(cp5_vs_csurtrac, fp, 'CP (S5) vs C-SURTRAC')

    with open('{}.{}.json'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        json.dump(table, fp, indent=4)

    plt.figure(figsize=(20,5))
    lines = plt.plot(case, fixed, ':.',
                     case, usurtrac, ':.',
                     case, csurtrac, ':.',
                     range(1, cp1_count+1), cp1, ':.',
                     range(1, cp5_count+1), cp5, ':.',
                     alpha=0.7)
    plt.legend(lines, ['Fixed', 'U-SURTRAC', 'C-SURTRAC', 'CP (S1)', 'CP (S5)'])
    plt.ylabel('Average Delay (s)')
    plt.title('{} network | {} runs'.format(args.net, count-1))
    plt.savefig('{}.delays.{}.png'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')))


if __name__ == '__main__':
    main()
