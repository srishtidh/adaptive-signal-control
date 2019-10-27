from __future__ import print_function

import os
import json
import argparse
import subprocess


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--labels', required=True,
                        help='Labels file')
    parser.add_argument('--config-dir', required=True,
                        help='Where to find SUMO config files')
    parser.add_argument('--log-dir', required=True,
                        help='Log directory')
    parser.add_argument('--info-file', required=True,
                        help='Path to TLS info file')
    parser.add_argument('--sample-count', type=int, default=1,
                        help='Number of samples to consider (default=1)')
    parser.add_argument('--coordinate', action='store_true', default=False,
                        help='Run experiments with coordination')
    parser.add_argument('--no-coord', action='store_true', default=False,
                        help='Run experiments without coordination')
    parser.add_argument('--timelimit', default=5,
                        help='Timelimit for scheduler')
    parser.add_argument('--scheduler', required=True, choices=['schic', 'cp', 'milp'],
                        help='Scheduler used by agent')
    parser.add_argument('--agent', required=True, choices=['Exp', 'SAA', 'SAANN', 'SURTRAC'],
                        help='Adaptive agent to run')
    parser.add_argument('--samples', required=True,
                        help='Sample set to run')
    parser.add_argument('--sample-set', required=True, type=int,
                        help='Sample set ID')
    parser.add_argument('--save-output', action='store_true', default=False)
    args = parser.parse_args()
    return args


if __name__ == '__main__':

    args = get_args()
    
    with open(args.labels, 'r') as fp:
        labels = json.load(fp)

    utils_dir = '/home/srishtid/adaptive-signal-control/adasco/utils/runners/'

    for label in labels:

        if args.no_coord:
            print("===========================================================")
            print("Running uncoordinated experiment with label", label)
            cmd = ['python', os.path.join(utils_dir, 'run_adaptive.py'), '-i', args.info_file,
                                                                         '-c', label,
                                                                         '-l', '{}-S{}-T{}-R{:03d}-uncoordinated'.format(label,
                                                                                                             args.sample_count,
                                                                                                             args.timelimit,
                                                                                                             args.sample_set),
                                                                         '--config-dir', args.config_dir,
                                                                         '--log-dir', args.log_dir,
                                                                         '--sample-count', str(args.sample_count),
                                                                         '--timelimit', args.timelimit,
                                                                         '--scheduler', args.scheduler,
                                                                         '--agent', args.agent,
                                                                         '--samples', args.samples]
            if args.save_output:
                cmd.append('--save-output')
            subprocess.call(cmd)

        if args.coordinate:
            print("===========================================================")
            print("Running coordinated experiment with label", label)
            cmd = ['python', os.path.join(utils_dir, 'run_adaptive.py'), '-i', args.info_file,
                                                                           '-c', label,
                                                                           '-l', '{}-S{}-T{}-R{:03d}-coordinated'.format(label,
                                                                                                                 args.sample_count,
                                                                                                                 args.timelimit,
                                                                                                                 args.sample_set),
                                                                               '--config-dir', args.config_dir,
                                                                               '--log-dir', args.log_dir,
                                                                               '--sample-count', str(args.sample_count),
                                                                               '--coordinate',
                                                                               '--timelimit', args.timelimit,
                                                                               '--scheduler', args.scheduler,
                                                                               '--agent', args.agent,
                                                                               '--samples', args.samples]
            if args.save_output:
                cmd.append('--save-output')
            subprocess.call(cmd)
