from __future__ import print_function
from __future__ import division

from collections import namedtuple
import os
import sys
import json
import pickle
import multiprocessing
import argparse
import logging
import subprocess
import importlib

import sumolib

import adasco.master
import adasco.registry

logger = logging.getLogger(__name__)

Turn = namedtuple('Turn', ['in_edge', 'outflows', 'probabilities'])
Outflow = namedtuple('Outflow', ['out_edge', 'phase'])


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--info-file', required=True,
                        help='Initialization data file for traffic light agents')
    parser.add_argument('--gui', action='store_true',
                        default=False, help='Run the GUI version of SUMO')
    parser.add_argument('-l', '--label',
                        help='Experiment label, used for naming output files')
    parser.add_argument('-c', '--config', required=True,
                        help="Config label, used for fetching appropriate input files")
    parser.add_argument('-o', '--save-output', action='store_true',
                        default=False, help='Save per-step variables and decisions')
    parser.add_argument("--config-dir", default='',
                        help="Directory that contains SUMO config files")
    parser.add_argument('--log-dir', default='',
                        help='Directory for outputting log files')
    parser.add_argument('-p', '--port', type=int,
                        default=sumolib.miscutils.getFreeSocketPort(),
                        help='Port for SUMO server')
    parser.add_argument('--coordinate', action='store_true',
                        default=False, help='Coordinate with neighbours')
    parser.add_argument('--sample-count', type=int, default=1,
                        help='Number of samples to pick per decision point')
    parser.add_argument('--timelimit', type=int, default=5,
                        help='Time limit for CP scheduler')
    parser.add_argument('--samples', nargs='+', required=True,
                        help='Pickled sample sets')
    parser.add_argument('--scheduler', required=True, choices=['schic', 'cp', 'milp'],
                        help='Scheduler type')
    parser.add_argument('--agent', required=True, choices=['Exp', 'Heuristic', 'SAA', 'SAANN', 'Hindsight', 'SURTRAC'],
                        help='Adaptive agent to run')
    options = parser.parse_args()
    return options


def start_sumo(config_file, log_file, trip_file, additional_file, port):
    args = ['sumo', '-c', config_file,
                    '--log-file', log_file,
                    '--tripinfo-output', trip_file,
                    '--additional-files', additional_file,
                    '--remote-port', str(port),
                    '--device.emissions.probability', str(1),
                    '--verbose',
                    '--duration-log.statistics',
                    '--time-to-teleport', '-1']
    subprocess.call(args)
    print("Started SUMO server")


def main():

    options = get_args()

    label = options.label if options.label else options.config

    prefix = '.{}.{}'.format(options.scheduler, options.agent.lower())

    config_dir = os.path.abspath(options.config_dir)
    config_file = os.path.join(config_dir, options.config + '.sumocfg')
    additional_file = os.path.join(config_dir, label + prefix + '.additional.xml')
    
    log_dir = os.path.abspath(options.log_dir)
    log_file = os.path.join(log_dir, label + prefix + '.summary.log')
    trip_file = os.path.join(log_dir, label + prefix + '.trip.xml')
    tls_switch_file = os.path.join(log_dir, label + prefix + '.tlsSwitch.xml')
    
    if options.save_output:
        debug_file = os.path.join(log_dir, label + prefix + '.log')
        logging.basicConfig(filename=debug_file, level=logging.DEBUG)

    with open(options.info_file, 'r') as fp:
        info = json.load(fp)

    with open(additional_file, 'w') as fp:
        fp.write('<additional>')
        for tlsID in info:
            fp.write('<timedEvent type="SaveTLSSwitchStates" source="{}" dest="{}"/>'.format(tlsID, tls_switch_file))
        fp.write('</additional>')    

    sumo_server = multiprocessing.Process(target=start_sumo, args=(config_file,
                                                                   log_file,
                                                                   trip_file,
                                                                   additional_file,
                                                                   options.port))
    sumo_server.start()

    logger.debug("Loaded tlsinfo")

    sets = []
    for sample_set in options.samples:
      with open(sample_set, 'r') as fp:
          samples = pickle.load(fp)
          sets.append(samples)

    processes = []

    manager = multiprocessing.Manager()
    shared_results = manager.dict()
    shared_lock = multiprocessing.Lock()

    registry = adasco.registry.Registry()

    agent_module = importlib.import_module('adasco.agents.{}.{}'.format(options.scheduler, options.agent.lower()))
    agent_class = getattr(agent_module, '{}Agent'.format(options.agent))

    for tls in info:

        shared_results[tls] = manager.dict()

        Y = {int(phase):value for phase, value in info[tls]['Y'].items()}
        Gmin = {int(phase):value for phase, value in info[tls]['Gmin'].items()}
        Gmax = {int(phase):value for phase, value in info[tls]['Gmax'].items()}

        request_queue = multiprocessing.JoinableQueue()
        response_queue = multiprocessing.JoinableQueue()

        process = agent_class(ID=info[tls]['id'],
                              phases=info[tls]['phases'],
                              Y=Y,
                              Gmin=Gmin,
                              Gmax=Gmax,
                              incoming_edges=info[tls]['incoming_edges'],
                              outgoing_edges=info[tls]['outgoing_edges'],
                              edge_lengths=info[tls]['edge_lengths'],
                              turn_proportions=info[tls]['turn_proportions'],
                              upstream_agents=info[tls]['upstream_agents'],
                              startup_lost_time=info[tls]['startup_lost_time'],
                              free_flow_speed=info[tls]['free_flow_speed'],
                              headway=info[tls]['headway'],
                              saturation_flow_rate=info[tls]['saturation_flow_rate'],
                              time_resolution=info[tls]['time_resolution'],
                              sampling_interval=info[tls]['sampling_interval'],
                              merging_threshold=info[tls]['merging_threshold'],
                              horizon_extension=info[tls]['horizon_extension'],
                              extension_threshold=info[tls]['extension_threshold'],
                              minimum_extension=info[tls]['minimum_extension'],
                              shared_results_directory=shared_results,
                              shared_lock=shared_lock,
                              publish_directory=shared_results[tls],
                              coordinate=options.coordinate,
                              request_queue=request_queue,
                              response_queue=response_queue,
                              sample_count=options.sample_count,
                              timelimit=options.timelimit,
                              samples=sets)

        processes.append(process)

        first_phase = info[tls]['phases'][0]
        entry = adasco.registry.Entry(process,
                                      request_queue,
                                      response_queue,
                                      None,
                                      0,
                                      Gmin[first_phase])
        registry.append(entry)

    master = adasco.master.Master(options.port, registry)
    processes.append(master)

    for process in processes:
        process.start()

    for process in processes:
        process.join()

if __name__ == '__main__':
    main()
