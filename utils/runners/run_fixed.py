from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import json
import argparse

from sumolib import checkBinary
import traci
import sumolib


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gui', action='store_true',
                        default=False, help='Run the GUI version of sumo')
    parser.add_argument('-l', '--label', action='store',
                        help='Experiment label, if different from config label')
    parser.add_argument('-c', '--config', action='store', required=True,
                        help='Config label, used for fetching appropriate input files')
    parser.add_argument('--config-dir', action='store', default='',
                        help='Directory that contains SUMO config files')
    parser.add_argument('--log-dir', action='store', default='',
                        help='Directory for outputting log files')
    parser.add_argument('--info-file', action='store', required=True,
                        help='TLS info file (for creating tls_switch_file)')
    parser.add_argument('-p', '--port', action='store', type=int,
                        default=sumolib.miscutils.getFreeSocketPort(),
                        help='Port for SUMO server')
    args = parser.parse_args()
    return args


def run():
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
    traci.close()
    sys.stdout.flush()


def main():
    args = get_args()

    if args.gui:
        sumoBinary = checkBinary('sumo-gui')
    else:
        sumoBinary = checkBinary('sumo')

    label = args.label if args.label else args.config

    config_dir = os.path.abspath(args.config_dir)
    config_file = os.path.join(config_dir, args.config + '.sumocfg')
    additional_file = os.path.join(config_dir, label + '.fixed.additional.xml')

    log_dir = os.path.abspath(args.log_dir)
    log_file = os.path.join(log_dir, label + '.fixed.summary.log')
    trip_file = os.path.join(log_dir, label + '.fixed.trip.xml')
    tls_switch_file = os.path.join(log_dir, label + '.fixed.tlsSwitch.xml')

    with open(args.info_file, 'r') as fp:
        info = json.load(fp)

    with open(additional_file, 'w') as fp:
        print('<additional>', file=fp)
        for tlsID in info:
            print('<timedEvent type="SaveTLSSwitchStates" source="{}" dest="{}"/>'.format(tlsID, tls_switch_file), file=fp)
        print('</additional>', file=fp)

    traci.start([sumoBinary, '-c', config_file,
                             '--log-file', log_file,
                             '--verbose',
                             '--duration-log.statistics',
                             '--tripinfo-output', trip_file,
                             '--additional-files', additional_file,
                             '--time-to-teleport', '-1'],
                port=args.port)

    run()


if __name__ == '__main__':
    main()