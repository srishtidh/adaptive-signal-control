from __future__ import print_function

from collections import namedtuple
from xml.etree.ElementTree import ParseError
import xml.etree.ElementTree as ET
import argparse
import itertools
import numpy as np
import tabulate
import json
import time
import os

Case = namedtuple('Case', ['tag', 'prefix', 'suffix'])

cases = [# Case(tag='fixed', prefix='', suffix='fixed'),
         Case(tag='surtrac-uncoo', prefix='-uncoordinated', suffix='heuristic'),
         Case(tag='surtrac-coord', prefix='-coordinated', suffix='heuristic'),
         Case(tag='cp-S1-TL5-uncoo', prefix='-S1-TL20-R001-uncoordinated', suffix='cp'),
         Case(tag='cp-S1-TL10-uncoo', prefix='-S1-TL40-R001-uncoordinated', suffix='cp'),
         Case(tag='cp-S1-TL20-uncoo', prefix='-S1-TL80-R001-uncoordinated', suffix='cp'),
         Case(tag='cp-S20-TL5-coord', prefix='-S20-TL20-R001-coordinated', suffix='cp'),
         Case(tag='cp-S50-TL5-coord', prefix='-S50-TL20-R001-coordinated', suffix='cp')]

header = ['#']
header.extend([case.tag for case in cases])

table = [header]

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--labels', required=True,
                        help='Experiment labels, input as a JSON file')
    parser.add_argument('--log-dir', required=True,
                        help='Log directory')
    parser.add_argument('-o', '--output-prefix', required=True,
                        help='Output prefix')
    args = parser.parse_args()
    return args


def get_delays_from_trips(trip_file):

    delays = []

    try:
        tree = ET.parse(trip_file)
    except (ParseError, IOError):
        return delays

    root = tree.getroot()

    for trip in root:
        delay = float(trip.get('waitSteps'))
        delays.append(delay)

    return delays


def get_median_delay(trip_file):
    print('Parsing {}'.format(trip_file))
    delays = get_delays_from_trips(trip_file)
    # print(delays)
    return np.median([delay for delay in delays if delay != np.nan])


def main():

    args = get_args()

    with open(args.labels, 'r') as fp:
        labels = json.load(fp)

    median_delays = {case.tag: [] for case in cases}

    for label in labels:
        for case in cases:
            trip_file = os.path.join(args.log_dir, 
                                     '{}{}.{}.trip.xml'.format(label,
                                                               case.prefix,
                                                               case.suffix))
            delay = get_median_delay(trip_file)
            median_delays[case.tag].append(get_median_delay(trip_file))

    for index, results in enumerate(itertools.izip_longest(*[median_delays[tag] for tag in header[1:]], fillvalue='-')):
        row = [index+1]
        row.extend(list(results))
        table.append(row)

    with open('{}.{}.median.log'.format(args.output_prefix, time.strftime('%d.%m.%Y.%H.%M.%S')), 'w') as fp:
        print(tabulate.tabulate(table, headers='firstrow', tablefmt='grid'), file=fp)


if __name__ == '__main__':
    main()