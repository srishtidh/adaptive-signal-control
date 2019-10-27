'''
Given a flow file, plot the demand
NOTE: UNTESTED!
'''

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import argparse
import json


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--flow-file', required=True,
                        help='Flow file to parse')
    parser.add_argument('-o', '--output-prefix', required=True,
                        help='Output prefix')
    args = parser.parse_args()
    return args


def parse_flows(flow_file, output_prefix):

    flows = {}

    tree = ET.parse(flow_file)
    root = tree.getroot()
    
    for element in root:
        if element.tag == 'flow':
            edge = element.get('from')
            begin = float(element.get('begin'))
            end = float(element.get('end'))
            rate = float(element.get('probability'))
            if edge not in flows:
                flows[edge] = {}
                flows[edge]['x'] = []
                flows[edge]['y'] = []
            flows[edge]['x'].append(begin)
            flows[edge]['y'].append(rate)
            flows[edge]['x'].append(end)
            flows[edge]['y'].append(rate)

    # print(flows)

    with open('{}.json'.format(output_prefix), 'w') as fp:
        json.dump(flows, fp, indent=4)

    flow_data = []
    for edge, data in flows.items():
        flow_data.append(data['x'])
        flow_data.append(data['y'])

    return flow_data

def plot_and_save_profile(flow_data, output_file):
    plt.plot(*flow_data, alpha=0.7)
    plt.xlabel('Time (s)')
    plt.ylabel('Probabability of emitting a vehicle each second')
    plt.title('Demand Profile')
    plt.savefig(output_file)


def main():
    args = get_args()
    flow_data = parse_flows(args.flow_file, args.output_prefix)
    plot_and_save_profile(flow_data, '{}.png'.format(args.output_prefix))


if __name__ == '__main__':
    main()