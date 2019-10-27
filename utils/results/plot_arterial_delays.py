from __future__ import print_function
from __future__ import division

from collections import namedtuple
import os
import time
import json
import pickle
import tabulate
import argparse
import itertools
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np

Case = namedtuple('Case', ['tag', 'prefix', 'suffix', 'subdir'])
Comparison = namedtuple('Comparison', ['name', 'base', 'hypothesis'])

cases = [
            Case(tag='surtrac-uncoo', prefix='-S1-T5-R001-uncoordinated', suffix='schic.surtrac', subdir=''),
            Case(tag='surtrac-coord', prefix='-S1-T5-R001-coordinated', suffix='schic.surtrac', subdir=''),
            Case(tag='cp-uncoo-S10-T5', prefix='-S10-T5-R001-uncoordinated', suffix='cp.saa', subdir=''),
            Case(tag='cp-coord-S10-T5', prefix='-S10-T5-R001-coordinated', suffix='cp.saa', subdir='')
        ]

comparisons = [
                   Comparison(name='csurtrac-vs-usurtrac', base='surtrac-uncoo', hypothesis='surtrac-coord'),
                   Comparison(name='ccpsaa-vs-ucpsaa-s10-t5', base='cp-uncoo-S10-T5', hypothesis='cp-coord-S10-T5'),
                   Comparison(name='ccpsaa-vs-csurtrac-s10-t5', base='surtrac-coord', hypothesis='cp-coord-S10-T5')
              ]
         
header = ['#', 'Label']
header.extend([case.tag for case in cases])

table = [header]


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--labels', required=True,
                        help='List of labels (as JSON file)')
    parser.add_argument('--log-dir', required=True,
                        help='Path to log directory')
    parser.add_argument('-o', '--output-prefix', required=True,
                        help='Output prefix')
    args = parser.parse_args()
    return args


# What if base is zero?
def perf_gain(base, hypothesis):
    return 100 * (hypothesis - base) / base


def _parse_delay(filename, arterial_vehicles):
    tree = ET.parse(filename)
    trips = tree.getroot()
    count = 0
    delay = 0
    for trip in trips:
        if trip.get('id') in arterial_vehicles:
            count += 1
            delay += float(trip.get('waitSteps'))
    return delay / count

def parse_and_store_delay(file, arterial_vehicles, delays):
    try:
        delay = _parse_delay(file, arterial_vehicles)
    except IOError:
        print('IOError while parsing {}'.format(file))
        return

    if delay is not None:
        delays.append(delay)


def main():
    args = get_args()
    
    with open(args.labels, 'r') as fp:
        labels = json.load(fp)
    
    delays = {case.tag: [] for case in cases}

    for index, label in enumerate(labels):
        with open(os.path.join(args.log_dir, '{}-arterial.json'.format(label))) as fp:
            arterial_vehicles = json.load(fp)
        for case in cases:
            log = os.path.join(args.log_dir, case.subdir, '{}{}.{}.trip.xml'.format(label, case.prefix, case.suffix))
            parse_and_store_delay(log, arterial_vehicles, delays[case.tag])

    for index, results in enumerate(itertools.izip_longest(*[delays[tag] for tag in header[2:]], fillvalue='-')):
        row = [index+1, labels[index]]
        row.extend(list(results))
        table.append(row)

    with open('{}.{}.log'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        print(tabulate.tabulate(table, headers='firstrow', tablefmt='grid'), file=fp)

    with open('{}.{}.json'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        json.dump(delays, fp, indent=4)

    # plt.rc('text', usetex=True)
    # plt.rc('font', family='serif')

    plt_args = []
    legend = []
    for case_tag, case_delays in delays.items():
        plt_args.extend([range(1, len(case_delays)+1), case_delays])
        legend.append(case_tag)

    plt.figure(figsize=(20, 10))
    lines = plt.plot(*plt_args, alpha=0.7)
    plt.legend(lines, legend)
    plt.ylabel(r'Average Delay (s)')
    plt.xlabel(r'Test case')
    plt.xticks(range(1, max([len(g) for g in delays.values()])+1))
    plt.title(r'Delays | {}'.format(args.output_prefix))
    plt.savefig('{}.delays.{}.png'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')))
    plt.close()

    results = []
    for comparison in comparisons:
        perf = [perf_gain(base, hypothesis) for base, hypothesis in zip(delays[comparison.base],
                                                                        delays[comparison.hypothesis])]

        if perf:
            summary = {'gains': perf,
                       'mean': np.mean(perf),
                       'stddev': np.std(perf),
                       'median': np.median(perf),
                       'runs': len(perf),
                       'label': '{}-R{}'.format(comparison.name, len(perf))}
            results.append(summary)
            with open('{}.{}.{}.json'.format(args.output_prefix, comparison.name, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
                json.dump(summary, fp, indent=4)

    plt.figure(figsize=(10, 10))
    graph = plt.boxplot([result['gains'] for result in results], showmeans=True, meanline=True)
    plt.legend((graph['means'][0], graph['medians'][0]), ('Mean', 'Median'))
    plt.xticks(range(1, len(results)+1), [result['label'] for result in results], rotation=10)
    plt.ylabel('% Change in Average Delay')
    plt.savefig('{}.boxplot.{}.png'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')))
    plt.close()

    plt.figure(figsize=(10, 10))
    plt.bar(x=[result['label'] for result in results],
            height=[result['mean'] for result in results],
            yerr=[result['stddev'] for result in results])
    plt.ylabel('% Change in Average Delay')
    plt.xticks(rotation=10)
    plt.savefig('{}.bar.{}.png'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')))
    plt.close()

    with open('{}.cases.{}.pkl'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        pickle.dump(cases, fp)

    with open('{}.comparisons.{}.pkl'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        pickle.dump(comparisons, fp)

if __name__ == '__main__':
    main()
