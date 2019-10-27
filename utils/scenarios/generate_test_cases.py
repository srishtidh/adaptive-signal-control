from __future__ import print_function
from __future__ import division

from math import ceil

import os
import json
import time
import random
import argparse
import subprocess

import sumolib


def get_args():
    parser = argparse.ArgumentParser(description="Generate routes and sumocfg files for a particular flow")
    parser.add_argument("-r", "--runs", action="store", type=int, default=100,
                        help="Number of runs to generate for the flow file")
    parser.add_argument("--start", action="store", type=int, default=1,
                        help="Starting number of labels")
    parser.add_argument("-n", "--net-file", action="store", required=True,
                        help="SUMO net file")
    parser.add_argument("-t", "--turn-file", action="store", required=True,
                        help="SUMO turns file")
    parser.add_argument("--label", action="store", required=True,
                        help="Label for flow file")
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    try:
        with open('labels.json', 'r') as fp:
            labels = json.load(fp)
    except IOError:
        labels = []

    flow_file = args.label + ".flow.xml"

    for run in range(args.runs):
        label = "{}-{:03d}".format(args.label, args.start+run)
        labels.append(label)
        route_file = label + ".rou.xml"
        config_file = label + ".sumocfg"
        generate_sumocfg(config_file, route_file, args.net_file)
        generate_routes(flow_file, route_file, args.net_file, args.turn_file)
        time.sleep(2)
    
    with open("labels.json", "w") as fp:
        json.dump(labels, fp, indent=4)


def generate_sumocfg(config_file, route_file, net_file):

    config_xml = sumolib.xml.create_document("configuration")

    input_element = config_xml.addChild("input")
    input_element.addChild("net-file", {"value": net_file})
    input_element.addChild("route-files", {"value": route_file})

    report_element = config_xml.addChild("report")
    report_element.addChild("verbose", {"value": "true"})
    report_element.addChild("duration-log.statistics", {"value": "true"})

    with open(config_file, "w") as fp:
        fp.write(config_xml.toXML())


def generate_routes(flow_file, route_file, net_file, turn_file):
    args = ["jtrrouter",
            "-n", net_file,
            # "-t", turn_file,
            "-r", flow_file,
            "-o", route_file,
            "--accept-all-destinations",
            "--departspeed", "max",
            "--departlane", "best",
            "--random",
            "--randomize-flows"]
    subprocess.call(args)


if __name__ == "__main__":
    main()
