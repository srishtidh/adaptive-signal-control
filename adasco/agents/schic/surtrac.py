from __future__ import print_function
from __future__ import division

from copy import deepcopy
import logging
import timeit

from adasco.cluster import ClusterSequence
from adasco.agents.base import BaseAgent
import adasco.schedulers.schic

logger = logging.getLogger(__name__)


class SURTRACAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super(SURTRACAgent, self).__init__(*args, **kwargs)
        self.scheduler = adasco.schedulers.schic.SchIC(self.phases,
                                                         self.Gmin,
                                                         self.Gmax,
                                                         self.Y,
                                                         self.startup_lost_time)

    def switch_back(self, phase):
        min_cycle = sum(self.Gmin.values()) + sum(self.Y.values())
        return min_cycle - self.Gmin[phase]

    def count_to_ratio(self, road_count):
        road_ratio = {}
        for phase, arrivals in road_count.items():
            road_ratio[phase] = {}
            for arrival, splits in arrivals.items():
                road_ratio[phase][arrival] = {}
                total = sum(splits.values())
                road_ratio[phase][arrival] = {edge: (count / total)
                                              for edge, count in splits.items()}
        return road_ratio

    # TODO(srishtid): Simplify this!
    def publish_results(self, inflow, outflow, phase_sequence, road_ratio):
        outflow_by_edge = {}
        curr_cluster = {phase:0 for phase in inflow}
        for outgoing_cluster, phase in zip(outflow, phase_sequence):
            original_cluster = inflow[phase][curr_cluster[phase]]
            curr_cluster[phase] += 1
            for incoming_edge, split_ratio in road_ratio[phase][original_cluster.arrival].items():
                turns_from_edge = self._get_normalized_turn_ratios(incoming_edge, phase)
                for turn in turns_from_edge:
                    outgoing_edge = turn['outgoing_edge']
                    turn_probability = turn['probability']
                    outflow_to_edge = outgoing_cluster.expected_proportion(split_ratio*turn_probability, self.min_cluster_size)
                    if outflow_to_edge:
                        try:
                            outflow_by_edge[outgoing_edge].insort(outflow_to_edge, merge=True)
                        except KeyError:
                            outflow_by_edge[outgoing_edge] = ClusterSequence([outflow_to_edge])
                    else:
                        pass
        
        with self.shared_lock:
            self.publish_directory.clear()
            for edge, outflow in outflow_by_edge.items():
                self.publish_directory[edge] = outflow
            self.shared_results_directory[self.id] = self.publish_directory

    def _get_normalized_turn_ratios(self, incoming_edge, phase):
        normalized_turns = []
        turns_from_edge = [turn for turn in self.turn_proportions
                           if turn['phase'] == phase
                           and turn['incoming_edge'] == incoming_edge]
        total_outflow = sum([turn['probability'] for turn in turns_from_edge])
        # Normalize turn probabilities
        for turn in turns_from_edge:
            normalized_turn = {}
            normalized_turn['incoming_edge'] = turn['incoming_edge']
            normalized_turn['outgoing_edge'] = turn['outgoing_edge']
            normalized_turn['phase'] = turn['phase']
            normalized_turn['probability'] = turn['probability'] / total_outflow
            normalized_turns.append(normalized_turn)
        return normalized_turns

    def plan(self, sensor_data, curr_phase, curr_phase_duration, curr_time):

        # Is this value actually being used? Where?
        self.min_cluster_size = 0.0001

        logger.debug('Queue length = {}'.format([data.queue_length for edge, data in sensor_data.items()]))

        start_plan = timeit.default_timer()

        roadflow = self.preprocessor.get_roadflow(sensor_data)
        
        for edge, sequence in roadflow.items():
            sequence.shift(curr_time)
                
        if self.coordinate:
            self.add_non_local_observation(roadflow, curr_time)
        
        inflow, road_count = self.preprocessor.get_inflow_from_roadflow(roadflow,
                                                                        self.phases,
                                                                        self.turn_proportions)
        
        # Aggregate by threshold
        for phase, sequence in inflow.items():
            merged_arrivals = sequence.merge_by_threshold(self.merging_threshold)
            for head_arrival, tail_arrivals in merged_arrivals.items():
                for arrival in tail_arrivals:
                    for edge, vehicle_count in road_count[phase][arrival].items():
                        try:
                            road_count[phase][head_arrival][edge] += vehicle_count
                        except KeyError:
                            road_count[phase][head_arrival][edge] = vehicle_count
                    road_count[phase].pop(arrival)

        road_ratio = self.count_to_ratio(road_count)

        cluster_count = sum([len(sequence) for sequence in inflow.values()])

        if cluster_count > 0:
            outflow, phase_sequence, phase_duration, updated_inflow, updated_road_ratio = self.get_feasible_control_flow(inflow,
                                                                                                                         curr_phase,
                                                                                                                         curr_phase_duration,
                                                                                                                         curr_time,
                                                                                                                         road_ratio)

            time_plan = timeit.default_timer() - start_plan
            logger.debug('Time for planning = {}'.format(time_plan))

            if phase_sequence[0] != curr_phase or inflow[curr_phase][0].arrival >= (curr_time + self.switch_back(curr_phase)):
                extension = 0
                decision_point = curr_time + self.Y[curr_phase] + self.Gmin[self.get_next_phase(curr_phase)]
            else:
                planned_extension = outflow[0].departure - curr_time
                allowed_extension = min(self.Gmax[curr_phase] - curr_phase_duration,
                                        self.extension_threshold,
                                        planned_extension)
                if allowed_extension > 0:
                    extension = int(round(allowed_extension))
                    decision_point = curr_time + extension
                else:
                    extension = 0
                    decision_point = curr_time + self.Y[curr_phase] + self.Gmin[self.get_next_phase(curr_phase)]

            if self.coordinate:
                # TODO: Store road_ratio with the clusters
                # TODO: Split functions (publish_results is doing a lot more than publishing at the moment); pass only exact outflow to publish
                self.publish_results(updated_inflow, outflow, phase_sequence, updated_road_ratio)

        else:
            extension = 0
            decision_point = curr_time + self.Y[curr_phase] + self.Gmin[self.get_next_phase(curr_phase)]

        return extension, decision_point

    def add_non_local_observation(self, roadflow, curr_time):
        for agent in self.upstream_agents:
            
            incoming_edge = agent['connecting_edge']
            agent_id = agent['id']
            
            with self.shared_lock:
                try:
                    outflow = self.shared_results_directory[agent_id][incoming_edge]
                except KeyError:
                    continue
                    
            extension = outflow.slice(curr_time, curr_time + self.horizon_extension, self.min_cluster_size)
            lane_traversal_time = self.edge_lengths[incoming_edge] / self.free_flow_speed
            extension.shift(lane_traversal_time)
    
            try:
                roadflow[incoming_edge] = roadflow[incoming_edge].merge(extension)
            except KeyError:
                roadflow[incoming_edge] = extension

    def get_feasible_control_flow(self, inflow, curr_phase, curr_phase_duration, curr_time, road_ratio):
 
        outflow = ClusterSequence()
        phase_sequence = []
        phase_duration = []
        updated_inflow = {phase: ClusterSequence() for phase in inflow}
        updated_road_ratio = {phase: {} for phase in inflow}
        
        violation_time = None
        
        tmp_curr_phase = curr_phase
        tmp_curr_phase_duration = curr_phase_duration
        tmp_curr_time = curr_time
        tmp_inflow = {phase: sequence.copy() for phase, sequence in inflow.items()}

        while violation_time != float('inf'):

            violation_time = float('inf')
            tmp_outflow, tmp_phase_sequence, tmp_phase_duration = self.scheduler.schedule(tmp_inflow,
                                                                                          tmp_curr_phase,
                                                                                          tmp_curr_phase_duration,
                                                                                          tmp_curr_time)
            
            curr_index = 0

            for cluster, phase, duration in zip(tmp_outflow, tmp_phase_sequence, tmp_phase_duration):
                cluster_from_inflow = tmp_inflow[phase][0]
                if duration > self.Gmax[phase]:
                    violation_time = cluster.departure - (duration - self.Gmax[phase])
                    if violation_time < cluster.arrival:
                        if curr_index == 0:
                            violation_time = tmp_curr_time
                        else:
                            previous_cluster = tmp_outflow[curr_index-1]
                            violation_time = previous_cluster.departure

                    unviolated_outflow, violated_outflow = cluster.split(violation_time, self.min_cluster_size)
                    unviolated_ratio = 1 - (violated_outflow.count / cluster.count)
                    unviolated_inflow, violated_inflow = cluster_from_inflow.split_by_ratio(unviolated_ratio, self.min_cluster_size)

                    tmp_inflow[phase].set(0, violated_inflow)
                    road_ratio[phase][violated_inflow.arrival] = road_ratio[phase][cluster_from_inflow.arrival]

                    if unviolated_outflow:

                        outflow.append(unviolated_outflow)
                        phase_sequence.append(phase)
                        phase_duration.append(self.Gmax[phase])
                        updated_inflow[phase].append(unviolated_inflow)
                        updated_road_ratio[phase][unviolated_inflow.arrival] = road_ratio[phase][cluster_from_inflow.arrival]

                    tmp_curr_time = violation_time + self.Y[phase]
                    tmp_curr_phase = self.get_next_phase(phase)
                    tmp_curr_phase_duration = 0

                    break
                else:
                    outflow.append(cluster)
                    phase_sequence.append(phase)
                    phase_duration.append(duration)
                    scheduled_cluster = tmp_inflow[phase].pop(0)
                    if scheduled_cluster:
                        updated_inflow[phase].append(scheduled_cluster)
                        updated_road_ratio[phase][scheduled_cluster.arrival] = deepcopy(road_ratio[phase][cluster_from_inflow.arrival])

                curr_index += 1

        return outflow, phase_sequence, phase_duration, updated_inflow, updated_road_ratio
