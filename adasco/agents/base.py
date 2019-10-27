from __future__ import print_function
from __future__ import division

import multiprocessing
import logging

from adasco.cluster import ClusterSequence
import adasco.preprocessor
import adasco.messaging

logger = logging.getLogger(__name__)


class BaseAgent(multiprocessing.Process):
    # TODO(srishtid): Find a better way to deal with kwargs
    # TODO(srishtid): Change data type of turn proportions
    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self)
        self.id = kwargs.get('ID')
        self.phases = kwargs.get('phases')
        self.Y = kwargs.get('Y')
        self.Gmin = kwargs.get('Gmin')
        self.Gmax = kwargs.get('Gmax')
        self.incoming_edges = kwargs.get('incoming_edges')
        self.outgoing_edges = kwargs.get('outgoing_edges')
        self.edge_lengths = kwargs.get('edge_lengths')
        self.turn_proportions = kwargs.get('turn_proportions')
        self.upstream_agents = kwargs.get('upstream_agents')
        self.startup_lost_time = kwargs.get('startup_lost_time')
        self.free_flow_speed = kwargs.get('free_flow_speed')
        self.headway = kwargs.get('headway')
        self.saturation_flow_rate = kwargs.get('saturation_flow_rate')
        self.time_resolution = kwargs.get('time_resolution')
        self.sampling_interval = kwargs.get('sampling_interval')
        self.merging_threshold = kwargs.get('merging_threshold')
        self.horizon_extension = kwargs.get('horizon_extension')
        self.extension_threshold = kwargs.get('extension_threshold')
        self.minimum_extension = kwargs.get('minimum_extension')
        self.shared_results_directory = kwargs.get('shared_results_directory')
        self.shared_lock = kwargs.get('shared_lock')
        self.publish_directory = kwargs.get('publish_directory')
        self.request_queue = kwargs.get('request_queue')
        self.response_queue = kwargs.get('response_queue')
        self.min_cluster_size = 0.1
        self.coordinate = kwargs.get('coordinate')
        self.preprocessor = adasco.preprocessor.ExactPreprocessor(self.saturation_flow_rate,
                                                                  self.free_flow_speed,
                                                                  self.time_resolution,
                                                                  self.sampling_interval,
                                                                  self.min_cluster_size,
                                                                  self.merging_threshold)

    def get_next_phase(self, phase):
        phase_index = self.phases.index(phase)
        next_phase_index = (phase_index + 1) % len(self.phases)
        return self.phases[next_phase_index]

    def run(self):
        while True:
            request = self.request_queue.get()
            
            if request.code == adasco.messaging.KILL:
                break

            extension, decision_point = self.plan(request.sensor_data,
                                                  request.curr_phase,
                                                  request.curr_phase_duration,
                                                  request.curr_time)

            response = adasco.messaging.Response(extension, decision_point)
            self.response_queue.put(response)

            self.request_queue.task_done()

    def plan(self, sensor_data, curr_phase, curr_phase_duration, curr_time):
        pass
