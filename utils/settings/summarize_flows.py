import json
import argparse
import xml.etree.ElementTree as ET


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--flow-file', required=True, help='Flow file')
    parser.add_argument('--output-file', required=True, help='Output file')
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    tree = ET.parse(args.flow_file)
    root = tree.getroot()

    flows = []
    for element in root:
    	if element.tag != 'flow':
    		continue
        origin = element.get('from')
        destination = element.get('to')
        via = element.get('via')
        if via is None:
            via = ''
        route = ' '.join([origin, via, destination])
    	flow = {'id': element.get('id'),
    	        'count': int(element.get('number')),
    	        'route': route}
    	flows.append(flow)

    with open(args.output_file, 'w') as fp:
    	json.dump(flows, fp, indent=4)


if __name__ == '__main__':
 	main()
