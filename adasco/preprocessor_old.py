from __future__ import print_function
from __future__ import division

from collections import namedtuple
from operator import attrgetter
from copy import deepcopy
import logging

import numpy as np

from adasco.cluster import Cluster, ClusterSequence

logger = logging.getLogger(__name__)


class ExactPreprocessor(object):
    def __init__(self,
                 saturation_flow_rate,
                 free_flow_speed,
                 time_resolution,
                 sampling_interval,
                 min_cluster_size,
                 merging_threshold):
        self.saturation_flow_rate = saturation_flow_rate
        self.free_flow_speed = free_flow_speed
        self.time_resolution = time_resolution
        self.sampling_interval = sampling_interval
        self.min_cluster_size = min_cluster_size
        self.merging_threshold = merging_threshold

    def get_queue_cluster(self, queue_length):
        if queue_length == 0:
            return None
        count = queue_length
        arrival = 0
        duration = count / self.saturation_flow_rate
        departure = self.round_to_delta(arrival + duration)
        queue_cluster = Cluster(count=count,
                                arrival=arrival,
                                departure=departure)
        return queue_cluster

    def position_to_estimated_arrival_time(self, distance_to_junction):
        travel_time = distance_to_junction / self.free_flow_speed
        estimated_arrival_time = self.round_to_delta(travel_time)
        return estimated_arrival_time

    def get_arrival_times(self, distances_to_junction):
        return map(self.position_to_estimated_arrival_time, distances_to_junction)

    def round_to_delta(self, time):
        return round(time / self.time_resolution) * self.time_resolution

    def get_arriving_clusters(self, arrivals):
        tally = {}
        arriving_clusters = ClusterSequence()
        for arrival in arrivals:
            bucket = arrival // self.sampling_interval
            try:
                tally[bucket] += 1
            except KeyError:
                tally[bucket] = 1
        for bucket, count in tally.items():
            arriving_clusters.insort(Cluster(count=count,
                                             arrival=bucket*self.sampling_interval,
                                             departure=(bucket+1)*self.sampling_interval))
        return arriving_clusters

    def cluster_sensor_data(self, queue_length, vehicle_positions):
        queue_cluster = self.get_queue_cluster(queue_length)
        arrival_times = self.get_arrival_times(vehicle_positions)
        arriving_clusters = self.get_arriving_clusters(arrival_times)
        return queue_cluster, arriving_clusters

    def get_roadflow(self, sensor_data):
        roadflow = {}

        for edge, data in sensor_data.items():
            queue_cluster, arriving_clusters = self.cluster_sensor_data(data.queue_length,
                                                    data.arriving_vehicle_positions)
            # TODO(srishtid): Keep queue cluster for anticipated queue cluster
            if queue_cluster:
                arriving_clusters.insort(queue_cluster, merge=True)
            roadflow[edge] = arriving_clusters
        return roadflow

    def get_inflow_from_roadflow(self, roadflow, phases, turn_proportions):
        # Warning: road_to_phase doesn't return edge_inflow for every phase
        #          Only for phases relevant to the edge
        inflow = {phase: ClusterSequence() for phase in phases}
        road_count = {}
        for edge, edge_roadflow in roadflow.items():
            if edge_roadflow:
                edge_inflow = self.road_to_phase(edge,
                                                 edge_roadflow,
                                                 turn_proportions)
                for phase, clusters in edge_inflow.items():
                    inflow[phase] = inflow[phase].merge(clusters)
                    if phase not in road_count:
                        road_count[phase] = {}
                    for cluster in clusters:
                        if cluster.arrival not in road_count[phase]:
                            road_count[phase][cluster.arrival] = {}
                        try:
                            road_count[phase][cluster.arrival][edge] += cluster.count
                        except KeyError:
                            road_count[phase][cluster.arrival][edge] = cluster.count

        return inflow, road_count

    def road_to_phase(self, edgeID, roadflow, turn_proportions):

        inflow = {}
        turns_by_phase = {}
        turns_from_edge = [turn for turn in turn_proportions
                           if turn['incoming_edge'] == edgeID]

        for turn in turns_from_edge:
            phase = turn['phase']
            try:
                turns_by_phase[phase] = min(turns_by_phase[phase] + turn['probability'], 1)
            except KeyError:
                turns_by_phase[phase] = min(turn['probability'], 1)
                inflow[phase] = ClusterSequence()

        for cluster in roadflow:
            for phase, ratio in turns_by_phase.items():
                split = cluster.expected_proportion(ratio, self.min_cluster_size)
                if split:
                    inflow[phase].insort(split, merge=True)

        return inflow

    # TODO: Create vehicle objects before this function is called
    def get_queued_clusters_from_positions(self, vehicle_positions, outgoing_edges, IDs):

        arrival_times = self.get_arrival_times(vehicle_positions)

        queued_clusters = ClusterSequence()
        queued_cluster_info = {}

        queue_length = len(arrival_times)
        queue_arrival = 0
        queue_duration = queue_length / self.saturation_flow_rate
        queue_departure = self.round_to_delta(queue_arrival + queue_duration)
        queue_cluster = Cluster(count=queue_length,
                                arrival=queue_arrival,
                                departure=queue_departure)

        queued_clusters.insort(queue_cluster, merge=True)

        for vehID, arrival, outgoing_edge in zip(IDs, arrival_times, outgoing_edges):
            try:
                queued_cluster_info[queue_arrival].append(VehicleInfo(vehID, arrival, outgoing_edge))
            except KeyError:
                queued_cluster_info[queue_arrival] = [VehicleInfo(vehID, arrival, outgoing_edge)]

        return queued_clusters, queued_cluster_info

    def get_arriving_clusters_from_positions(self, vehicle_positions, outgoing_edges, IDs):

        arrivals = self.get_arrival_times(vehicle_positions)

        tally = {}
        arriving_cluster_info = {}

        arriving_clusters = ClusterSequence()

        for vehID, arrival, outgoing_edge in zip(IDs, arrivals, outgoing_edges):
            bucket = arrival // self.sampling_interval
            try:
                tally[bucket] += 1
                arriving_cluster_info[bucket*self.sampling_interval].append(VehicleInfo(
                                                                                vehID,
                                                                                arrival,
                                                                                outgoing_edge
                                                                                )
                                                                            )
            except KeyError:
                tally[bucket] = 1
                arriving_cluster_info[bucket*self.sampling_interval] = [VehicleInfo(vehID, arrival, outgoing_edge)]

        for bucket, count in tally.items():
            arriving_clusters.insort(Cluster(count=count,
                                             arrival=bucket*self.sampling_interval,
                                             departure=(bucket+1)*self.sampling_interval))

        return arriving_clusters, arriving_cluster_info

    def pick_sample_for_sensor_data(self, sensor_data, samples, index, phases):
        
        sample = Sample(phases)

        for edge, data in sensor_data.items():
            edge_inflow_sample = self.pick_sample_for_edge(edge,
                                                           data,
                                                           samples,
                                                           index,
                                                           phases)
            sample.merge(edge_inflow_sample)

        sample.merge_by_threshold(self.merging_threshold)

        for cluster_info in sample.cluster_info.values():
            for vehicle_info in cluster_info.values():
                vehicle_info.sort(key=attrgetter('arrival'))
    
        return sample

    def pick_sample_for_edge(self, edgeID, data, samples, index, phases):

        sample = Sample(phases)
        print("\nedge id"+str(edgeID))
        vehicle_info_by_phase = {}
        for vehID, position in zip(data.queued_vehicle_ids, data.queued_vehicle_positions):
            sampled_turn = samples[vehID][edgeID][index]
            sampled_phase = sampled_turn.phase
            sampled_outgoing_edge = sampled_turn.out_edge

            if sampled_phase not in vehicle_info_by_phase:
                vehicle_info_by_phase[sampled_phase] = {'distances': [],
                                                        'outgoing_edges': [],
                                                        'IDs': []}

            vehicle_info_by_phase[sampled_phase]['distances'].append(position)
            vehicle_info_by_phase[sampled_phase]['outgoing_edges'].append(sampled_outgoing_edge)
            vehicle_info_by_phase[sampled_phase]['IDs'].append(vehID)

        for phase, vehicle_info in vehicle_info_by_phase.items():
            #print("\nvehicle info "+str(vehicle_info))
            queued_clusters, queued_cluster_info = self.get_queued_clusters_from_positions(vehicle_info['distances'],
                                                                                           vehicle_info['outgoing_edges'],
                                                                                           vehicle_info['IDs'])
            sample.add(phase, queued_clusters, queued_cluster_info)
        
        vehicle_info_by_phase = {}
        for vehID, position in zip(data.arriving_vehicle_ids, data.arriving_vehicle_positions):
            sampled_turn = samples[vehID][edgeID][index]
            sampled_phase = sampled_turn.phase
            sampled_outgoing_edge = sampled_turn.out_edge

            if sampled_phase not in vehicle_info_by_phase:
                vehicle_info_by_phase[sampled_phase] = {'distances': [],
                                                        'outgoing_edges': [],
                                                        'IDs': []}

            vehicle_info_by_phase[sampled_phase]['distances'].append(position)
            vehicle_info_by_phase[sampled_phase]['outgoing_edges'].append(sampled_outgoing_edge)
            vehicle_info_by_phase[sampled_phase]['IDs'].append(vehID)

        for phase, vehicle_info in vehicle_info_by_phase.items():
            arriving_clusters, arriving_cluster_info = self.get_arriving_clusters_from_positions(vehicle_info['distances'],
                                                                                                 vehicle_info['outgoing_edges'],
                                                                                                 vehicle_info['IDs'])
            sample.add(phase, arriving_clusters, arriving_cluster_info)

        return sample                    

class Sample(object):
    def __init__(self, phases, inflow=None, cluster_info=None):
        self.inflow = {phase: ClusterSequence() for phase in phases} if inflow is None else inflow
        self.cluster_info = {phase: {} for phase in phases} if cluster_info is None else cluster_info
        self.phases = sorted(phases)

    def __repr__(self):
        return '{}(inflow={}, cluster_info={})'.format(self.__class__.__name__,
                                                       self.inflow,
                                                       self.cluster_info)

    # Only compare inflows
    def __eq__(self, other):
        class_check = isinstance(other, self.__class__)
        phase_check = (other.phases == self.phases)
        equality_check = class_check and phase_check
        if equality_check:
            for phase in self.phases:
                equality_check = (equality_check and
                                  self.inflow[phase] == other.inflow[phase])
        return equality_check

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        inflow_list = []
        for phase in self.phases:
            inflow_list.append(phase)
            inflow_list.append(self.inflow[phase])
        return hash(tuple(inflow_list))

    @property
    def cluster_count(self):
        return sum([len(sequence) for sequence in self.inflow.values()])
        
    # TODO(srishtid): Safeguard against missing phase
    def add(self, phase, clusters, cluster_info):
        for cluster in clusters:
            key = cluster.arrival
            try:
                self.cluster_info[phase][key].extend(cluster_info[key])
            except KeyError:
                self.cluster_info[phase][key] = cluster_info[key]
            self.inflow[phase].insort(cluster, merge=True)

    def merge(self, sample):
        for phase, clusters in sample.inflow.items():
            self.add(phase, clusters, sample.cluster_info[phase])

    def merge_by_threshold(self, threshold):    
        for phase, clusters in self.inflow.items():
            merged_arrivals = clusters.merge_by_threshold(threshold)

            for head_arrival, tail_arrivals in merged_arrivals.items():
                for cluster_arrival in tail_arrivals:
                    cluster_info = self.cluster_info[phase].pop(cluster_arrival)
                    self.cluster_info[phase][head_arrival].extend(cluster_info)


VehicleInfo = namedtuple('VehicleInfo', ['ID', 'arrival', 'outgoing_edge'])
