import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--trip-file', required=True,
                        help='Trip file to parse')
    parser.add_argument('-o', '--output-label', required=True,
                        help='Output label')
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


def build_and_export_distribution_graph(departures, delays, output_label, trip_file):

    plt.plot(departures, delays, 'b:.', alpha=0.7)
    plt.xlabel('Departure time (s)')
    plt.ylabel('Delay (s)')
    plt.title(trip_file)

    plt.savefig('{}.delay.png'.format(output_label))

    boxplot = plt.boxplot(delays, showmeans=True, meanline=True)
    plt.legend([boxplot['means'][0], boxplot['medians'][0]], ['Mean', 'Median'])
    plt.xlabel('Trip')
    plt.ylabel('Delay (s)')
    plt.title(trip_file)

    plt.savefig('{}.delay.box.png'.format(output_label))


def main():

    args = get_args()

    departures, delays = parse_trips(args.trip_file)

    build_and_export_distribution_graph(departures,
                                        delays,
                                        args.output_label,
                                        args.trip_file)


if __name__ == '__main__':
    main()