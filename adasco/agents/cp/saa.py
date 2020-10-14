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

from adasco.agents.base import BaseAgent
from adasco.cluster import ClusterSequence
import adasco.schedulers.cp
import adasco.utils

logger = logging.getLogger(__name__)


class SAAAgent(BaseAgent):

    def __init__(self, *args, **kwargs):
        super(SAAAgent, self).__init__(*args, **kwargs)
        self.sample_count = kwargs.get('sample_count')
        self.timelimit = kwargs.get('timelimit')
        [self.samples] = kwargs.get('samples')
        self.cycle_count = 3
        self.scheduler = adasco.schedulers.cp.CP(self.phases,
                                                 self.Gmin,
                                                 self.Gmax,
                                                 self.Y,
                                                 self.startup_lost_time,
                                                 self.timelimit,
                                                 self.cycle_count)

    def plan(self, sensor_data, curr_phase, curr_phase_duration, curr_time):

        logger.debug('Queue length = {}'.format([data.queue_length for edge, data in sensor_data.items()]))

        start_plan = timeit.default_timer()

        samples = []

        if self.coordinate:
            non_local_samples = self.get_non_local_samples(curr_time)

        for index in range(self.sample_count):
            extended_sensor_data = deepcopy(sensor_data)
            
            if self.coordinate:
                for edge, edge_samples in non_local_samples.items():
                    if not edge_samples.empty():
                        non_local_arrivals = edge_samples.get()
                        
                        non_local_arrival_IDs = [arrival.ID for arrival in non_local_arrivals] 
                        extended_sensor_data[edge].arriving_vehicle_ids.extend(non_local_arrival_IDs)

                        non_local_arrival_times = [arrival.time for arrival in non_local_arrivals]
                        non_local_vehicle_positions = self.get_distance_from_junction(non_local_arrival_times)
                        extended_sensor_data[edge].arriving_vehicle_positions.extend(non_local_vehicle_positions)
            #print("index:"+str(index))
            sample = self.preprocessor.pick_sample_for_sensor_data(extended_sensor_data, self.samples, index, self.phases)

            cluster_count = sample.cluster_count
            if cluster_count == 0:
                break

            samples.append(sample)

        if cluster_count > 0:

            sample_tally = Counter(samples)
            inflows = []
            weights = []
            distinct_samples = []
            sample_groups = []

            for sample, count in sample_tally.items():
                inflows.append(sample.inflow)
                weights.append(count)
                distinct_samples.append(sample)
                sample_groups.append([s for s in samples if s == sample])

            extension, cluster_departures = self.scheduler.schedule_over_all_samples(inflows,
                                                                                     weights,
                                                                                     curr_phase,
                                                                                     curr_phase_duration,
                                                                                     status_file='{}-{}.json'.format(self.id.replace('/', ''), curr_time))

            time_plan = timeit.default_timer() - start_plan
            logger.debug('Time for planning = {}'.format(time_plan))

            extension = int(round(extension))

            if extension == 0:
                decision_point = curr_time + self.Y[curr_phase] + self.Gmin[self.get_next_phase(curr_phase)]
            else:
                extension = max(extension, self.minimum_extension)
                extension = min(extension, self.extension_threshold, self.Gmax[curr_phase] - curr_phase_duration)
                decision_point = curr_time + extension

            if self.coordinate:
                vehicle_departures = self.calculate_vehicle_departures(cluster_departures, sample_groups)
                self.publish_results(vehicle_departures, curr_time)

        else:
            if curr_phase not in self.Y:
                print("Y"+ str(self.Y))
            extension = 0
            decision_point = curr_time + self.Y[curr_phase] + self.Gmin[self.get_next_phase(curr_phase)]

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
            
            for sample in samples:
                departures = adasco.utils.slice(sample, curr_time, curr_time + self.horizon_extension)
                if departures:
                    for index, departure in enumerate(departures):
                        departures[index] = Departure(departure.ID, departure.time - curr_time + lane_traversal_time)
                    
                    non_local_samples[incoming_edge].put(departures)

        return non_local_samples

    def get_distance_from_junction(self, arrivals):
        return [time_to_junction * self.free_flow_speed for time_to_junction in arrivals]

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

                                if passing_vehicle.arrival < max_arrival_in_slice:
                                    start_time = passing_vehicle.arrival + delay
                                    edge = passing_vehicle.outgoing_edge
                                    vehicle_departure = Departure(passing_vehicle.ID, start_time)
                                    
                                    try:
                                        per_edge_sample_departures[edge].append(vehicle_departure)
                                    except KeyError:
                                        per_edge_sample_departures[edge] = [vehicle_departure]
                                    
                                    vehicles.pop(0)
                                else:
                                    break

                for edge, departures in per_edge_sample_departures.items():
                    if edge not in per_edge_vehicle_departures:
                        per_edge_vehicle_departures[edge] = []
                    per_edge_vehicle_departures[edge].append(departures)

        return per_edge_vehicle_departures

    # TODO: Create separate function for converting to absolute time
    def publish_results(self, departures, curr_time):
        
        for edge, samples in departures.items():
            for sample in samples:
                for index, departure in enumerate(sample):
                    sample[index] = Departure(departure.ID, departure.time + curr_time)

        # TODO: Simplify this
        with self.shared_lock:
            self.publish_directory.clear()
            for edge, samples in departures.items():
                self.publish_directory[edge] = samples
            self.shared_results_directory[self.id] = self.publish_directory


Departure = namedtuple('Departure', ['ID', 'time'])
