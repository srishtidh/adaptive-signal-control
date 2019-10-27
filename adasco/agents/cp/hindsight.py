from __future__ import print_function
from __future__ import division

from copy import deepcopy
from math import ceil
from collections import namedtuple
from collections import Counter
import logging
import timeit
import Queue
import pickle
import pprint

from adasco.agents.base import BaseAgent
from adasco.cluster import ClusterSequence
import adasco.schedulers.cp
import adasco.utils

logger = logging.getLogger(__name__)


class HindsightAgent(BaseAgent):

    def __init__(self, *args, **kwargs):
        super(HindsightAgent, self).__init__(*args, **kwargs)
        self.sample_count = kwargs.get('sample_count')
        self.timelimit = kwargs.get('timelimit')
        [self.samples] = kwargs.get('samples')
        self.cycle_count = self.get_naive_cycle_count()
        self.scheduler = adasco.schedulers.cp.CP(self.phases,
                                                 self.Gmin,
                                                 self.Gmax,
                                                 self.Y,
                                                 self.startup_lost_time,
                                                 self.timelimit,
                                                 self.cycle_count)
        self.actions = None
        self.max_extension = 5

    def plan(self, sensor_data, curr_phase, curr_phase_duration, curr_time):

        self.actions = []
        for extension in range(0, self.max_extension+1):
            if curr_phase_duration + extension <= self.Gmax[curr_phase]:
                self.actions.append(extension)

        samples = []

        if self.coordinate:
            non_local_samples = self.get_non_local_samples(curr_time)
            # logger.debug('{}: Received non-local samples = {}'.format(self.id, non_local_samples))

        start_sampling = timeit.default_timer()

        per_edge_samples = []

        for index in range(self.sample_count):
            # logger.debug('{}: Generating sample # {}'.format(self.id, index))

            tmp_sensor_data = deepcopy(sensor_data)

            if self.coordinate:
                for edge, edge_samples in non_local_samples.items():
                    if not edge_samples.empty():
                        non_local_arrivals = edge_samples.get()
                        # logger.debug('{}: Adding extension {} to sensor data'.format(self.id, non_local_arrivals))
                        
                        non_local_arrival_IDs = [arrival.ID for arrival in non_local_arrivals] 
                        tmp_sensor_data[edge].arriving_vehicle_ids.extend(non_local_arrival_IDs)

                        non_local_arrival_times = [arrival.time for arrival in non_local_arrivals]
                        non_local_vehicle_positions = self.get_distance_from_junction(non_local_arrival_times)
                        tmp_sensor_data[edge].arriving_vehicle_positions.extend(non_local_vehicle_positions)

            sample, per_edge_sample = self.preprocessor.pick_sample_for_sensor_data(tmp_sensor_data, self.samples, index, self.phases)

            cluster_count = sample.cluster_count
            if cluster_count == 0:
                break

            samples.append(sample)
            per_edge_samples.append(per_edge_sample)

        # with open('{}-{}.pkl'.format(self.id.replace('/', '-'), curr_time), 'w') as fp:
        #     pickle.dump(per_edge_samples, fp)

        # logger.debug('{}: Generated samples = {}'.format(self.id, samples))

        time_sampling = timeit.default_timer() - start_sampling

        if cluster_count > 0:
            # logger.debug('{}: Cluster count greater than zero; Planning now'.format(self.id))

            sample_tally = Counter(samples)

            start_cp = timeit.default_timer()

            departures = None
            best_action = None
            best_delay = float('inf')

            total_problems = 0
            eliminated_problems = 0
            delays = {}
            for sample in sample_tally:
                for action in self.actions:
                    delays[(sample, action)] = None
            
            for action in self.actions:
                total_delay = 0
                sample_id = 0
                print('Trying action = {}'.format(action))
                
                for sample, count in sample_tally.items():

                    total_problems += 1
                    print('Checking sample {}'.format(sample_id))
                    # print(sample)
                    sample_id += 1
                    
                    # pprint.pprint(delays)
                    if action > 0 and delays[(sample, action)] is not None:
                        eliminated_problems += 1
                        total_delay += delays[(sample, action)] * count
                        continue
                    
                    extension, delay, cluster_departures = self.scheduler.schedule_in_hindsight(sample.inflow,
                                                                                                curr_phase,
                                                                                                curr_phase_duration,
                                                                                                action)
                    print('Sample delay = {}, action = {}, extension = {}'.format(delay, action, extension))
                    total_delay += delay * count

                    if action > 0:
                        for proposed_action in range(action, int(round(extension))+1):
                            if (sample, proposed_action) in delays:
                                delays[(sample, proposed_action)] = delay
                
                # print('Action delay: {} Best delay so far: {}'.format(total_delay, best_delay))
                if total_delay <= best_delay:
                    # print('Found new best action')
                    best_action = action
                    departures = cluster_departures # Incorrect; these are departures for a single sample
                    best_delay = total_delay

                # print('')

            print('Best action = {}'.format(best_action))

            print('Eliminated {} / {} problems'.format(eliminated_problems, total_problems))

            time_cp = timeit.default_timer() - start_cp

            print('Took {} s to decide'.format(time_cp))

            extension = int(round(best_action))

            if extension == 0:
                decision_point = curr_time + self.Y[curr_phase] + self.Gmin[self.get_next_phase(curr_phase)]
            else:
                extension = max(extension, self.minimum_extension)
                extension = min(extension, self.extension_threshold, self.Gmax[curr_phase] - curr_phase_duration)
                decision_point = curr_time + extension

            if self.coordinate:
                vehicle_departures = self.calculate_vehicle_departures(cluster_departures, sample_groups)
                self.publish_results(vehicle_departures, curr_time)
                logger.debug('{}: Published results = {}'.format(self.id, self.shared_results_directory))

        else:
            # logger.debug('{}: No inflow, moving on to next phase'.format(self.id))
            extension = 0
            decision_point = curr_time + self.Y[curr_phase] + self.Gmin[self.get_next_phase(curr_phase)]

        # logger.debug('{}: New decision_point={}'.format(self.id, decision_point))

        return extension, decision_point

    def get_non_local_samples(self, curr_time):
        non_local_samples = {}

        for agent in self.upstream_agents:
            
            incoming_edge = agent['connecting_edge']
            agentID = agent['id']
            lane_traversal_time = self.edge_lengths[incoming_edge] / self.free_flow_speed

            non_local_samples[incoming_edge] = Queue.Queue()
            
            with self.shared_lock:
                try:
                    samples = self.shared_results_directory[agentID][incoming_edge]
                except KeyError:
                    continue
            
            # logger.debug('{}: Outflow samples from agent {} = {}'.format(self.id, agentID, samples))
            # logger.debug('{}: Obtaining slice {} : {}'.format(self.id, step, step + self.horizon_extension))
            
            for sample in samples:
                # logger.debug('{}: Processing sample {}'.format(self.id, sample))
                departures = adasco.utils.slice(sample, curr_time, curr_time + self.horizon_extension)
                if departures:
                    for index, departure in enumerate(departures):
                        departures[index] = Departure(departure.ID, departure.time - curr_time + lane_traversal_time)
                    # logger.debug('{}: Obtained slice after converting to relative time and adding lane_traversal_time = {}'.format(self.id, departures))
                    
                    non_local_samples[incoming_edge].put(departures)

        return non_local_samples

    # TODO: Create separate function for converting to absolute time
    # Why are we planing in relative time though? Easier?
    def publish_results(self, departures, curr_time):
        # logger.debug('''{}: Publishing results with the following params
        #     departures = {}
        #     step = {}'''.format(self.id, departures, step))
        
        for edge, samples in departures.items():
            for sample in samples:
                for index, departure in enumerate(sample):
                    sample[index] = Departure(departure.ID, departure.time + curr_time)

        # logger.debug('{}: departures after converting to absolute time = {}'.format(self.id, departures))

        # Ridiculous, circular assignments; simplify this!
        with self.shared_lock:
            self.publish_directory.clear()
            # Why not self.publish_directory = departures?
            for edge, samples in departures.items():
                self.publish_directory[edge] = samples
            self.shared_results_directory[self.id] = self.publish_directory

    # TODO: Simplify this function
    def calculate_vehicle_departures(self, departures, sample_groups):
        per_edge_vehicle_departures = {}

        for sample_departures, samples in zip(departures, sample_groups):

            for sample in samples:
                per_edge_sample_departures = {}

                for phase, inflow in sample.inflow.items():
                    for cluster_id, cluster in enumerate(inflow):
                        cluster_departures = sample_departures[phase][cluster_id]
                        vehicles = sample.cluster_info[phase][cluster.arrival]
                        scheduled_proportion = 0
                        for (departure, ratio) in cluster_departures:
                            delay = departure - cluster.arrival
                            scheduled_proportion += ratio
                            max_arrival_in_slice = cluster.arrival + scheduled_proportion * cluster.duration

                            while vehicles:
                                passing_vehicle = vehicles[0]

                                # L / LE? Missing vehicles?
                                if passing_vehicle.arrival < max_arrival_in_slice:
                                    start_time = passing_vehicle.arrival + delay
                                    edge = passing_vehicle.outgoing_edge
                                    vehicle_departure = Departure(passing_vehicle.ID, start_time)
                                    
                                    try:
                                        per_edge_sample_departures[edge].append(vehicle_departure)
                                    except KeyError:
                                        per_edge_sample_departures[edge] = [vehicle_departure]
                                    
                                    # Editing in-place okay; not needed for agent after this
                                    vehicles.pop(0)
                                else:
                                    break

                for edge, departures in per_edge_sample_departures.items():
                    if edge not in per_edge_vehicle_departures:
                        per_edge_vehicle_departures[edge] = []
                    per_edge_vehicle_departures[edge].append(departures)

        return per_edge_vehicle_departures

    def get_distance_from_junction(self, arrivals):
        return [time_to_junction * self.free_flow_speed for time_to_junction in arrivals]

    def get_naive_cycle_count(self):
        gmin = min(self.Gmin.values())
        gmax = max(self.Gmax.values())
        edge_length = max(self.edge_lengths.values())
        traversal_time = edge_length / self.free_flow_speed
        avg_phase_length = (gmin + gmax) / 2
        cycles = max(ceil(traversal_time / avg_phase_length), 3)
        return int(cycles)


Departure = namedtuple('Departure', ['ID', 'time'])
