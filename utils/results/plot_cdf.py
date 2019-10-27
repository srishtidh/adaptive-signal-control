from __future__ import division

from collections import Counter
import xml.etree.ElementTree as ET
import argparse

import matplotlib.pyplot as plt
import numpy as np


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--surtrac-unc',
                        help='Path to SURTRAC uncoo trip file')
    parser.add_argument('--surtrac-coo',
                        help='Path to SURTRAC coord trip file')
    parser.add_argument('--cp-unc',
                        help='Path to CP uncoo trip file')
    parser.add_argument('--cp-coo',
                        help='Path to CP coord trip file')
    parser.add_argument('--output-prefix',
                        help='Output prefix')
    args = parser.parse_args()
    return args


def parse_delays(trip_file):
    delays = []
    tree = ET.parse(trip_file)
    tripinfos = tree.getroot()
    for trip in tripinfos:
        delays.append(int(trip.get('waitSteps')))
    print(trip_file)
    print('Mean: {} s'.format(np.mean(delays)))
    print('Median: {} s'.format(np.median(delays)))
    print('Std deviation: {} s'.format(np.std(delays)))
    return delays


def calculate_cdf(delays):
    tally = Counter(delays)
    cumulative = []
    count = 0
    sorted_delays = sorted(tally.keys())
    for delay in sorted_delays:
        count += tally[delay]
        cumulative.append(count)
    total = max(cumulative)
    normalized = [count/total for count in cumulative]
    return sorted_delays, normalized


def plot_cdf(trip_file):
    delays = parse_delays(trip_file)
    delays, cdf = calculate_cdf(delays)
    [line] = plt.plot(delays, cdf)
    return line


def main():
    args = get_args()

    lines = []
    labels = []
    
    if args.surtrac_unc:
        surtrac_unc = plot_cdf(args.surtrac_unc)
        lines.append(surtrac_unc)
        labels.append('surtrac-unc')

    if args.surtrac_coo:
        surtrac_coo = plot_cdf(args.surtrac_coo)
        lines.append(surtrac_coo)
        labels.append('surtrac-coo')

    if args.cp_unc:
        cp_unc = plot_cdf(args.cp_unc)
        lines.append(cp_unc)
        labels.append('cp-unc')

    if args.cp_coo:
        cp_coo = plot_cdf(args.cp_coo)
        lines.append(cp_coo)
        labels.append('cp-coo')    
    
    plt.legend(tuple(lines), tuple(labels))
    plt.xlabel('Delay (s)')
    plt.ylabel('Probability')
    plt.title('{} | CDF of Vehicle Delays'.format(args.output_prefix))

    plt.savefig('{}.cdf.png'.format(args.output_prefix))


if __name__ == '__main__':
    main()
