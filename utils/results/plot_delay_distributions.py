import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import argparse
import json
import os


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--labels', required=True,
                        help='Experiment labels, input as a JSON file')
    parser.add_argument('--log-dir', required=True,
                        help='Log directory')
    args = parser.parse_args()
    return args


def parse_trips(trip_file):

    waitingTimes = []

    tree = ET.parse(trip_file)
    root = tree.getroot()

    for trip in root:
        departure = float(trip.get('depart'))
        delay = float(trip.get('waitSteps'))
        waitingTimes.append((departure, delay))

    waitingTimes.sort(key=lambda x: x[0])

    departures = [x[0] for x in waitingTimes]
    delays = [x[1] for x in waitingTimes]

    return departures, delays


def plot_delay_distribution(axis, title, departures, delays):

    axis.plot(departures, delays, 'b:.', alpha=0.7)
    axis.set_xlabel('Departure (s)')
    axis.set_ylabel('Delay (s)')
    axis.set_title(title)


def main():

    args = get_args()

    with open(args.labels, 'r') as fp:
        labels = json.load(fp)

    for label in labels:
        figure, axes = plt.subplots(1, 3, sharex='all', sharey='all', figsize=(15, 5))
        titles = ['Fixed', 'U-SURTRAC', 'CP (S1)'] # Removed C-SURTRAC
        trip_files = [os.path.join(args.log_dir, '{}.fixed.trip.xml'.format(label)),
                      os.path.join(args.log_dir, '{}-uncoordinated.heuristic.trip.xml'.format(label)),
                      # os.path.join(args.log_dir, '{}-coordinated.heuristic.trip.xml'.format(label)),
                      os.path.join(args.log_dir, '{}-S1-R001-uncoordinated.cp.trip.xml'.format(label))]
        for axis, trip_file, title in zip(axes, trip_files, titles):
            departures, delays = parse_trips(trip_file)
            plot_delay_distribution(axis, title, departures, delays)

        plt.savefig('{}.delay.png'.format(label))


if __name__ == '__main__':
    main()