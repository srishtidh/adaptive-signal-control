from __future__ import print_function
from __future__ import division

from collections import namedtuple
import logging

from adasco.cluster import Cluster, ClusterSequence

logger = logging.getLogger(__name__)

State = namedtuple('State', ['phase_duration',
                             'finish_time',
                             'delay',
                             'previous_phase'])


class SchIC(object):

    def __init__(self, phases, Gmin, Gmax, Y, startup_lost_time, optimization_horizon=float('inf')):
        self.phases = phases
        self.phase_count = len(phases)
        self.Gmin = Gmin
        self.Gmax = Gmax
        self.Y = Y
        self.startup_lost_time = startup_lost_time
        self.optimization_horizon = optimization_horizon
        
        self._min_switch = self._initialize_min_switch()

        self.state_groups = {}
        self.start_times = {}

    def _initialize_min_switch(self):
        min_switch = {phase: {} for phase in self.phases}
        for base_phase in self.phases:
            min_switch[base_phase][base_phase] = 0
            curr_phase = base_phase
            switch_time = 0

            for index in range(self.phase_count - 1):
                next_phase = self._get_next_phase(curr_phase)
                
                switch_time += self.Y[curr_phase]
                if curr_phase != base_phase:
                    switch_time += self.Gmin[curr_phase]
                
                min_switch[base_phase][next_phase] = switch_time
                curr_phase = next_phase

        return min_switch

    def _get_next_phase(self, curr_phase):
        curr_phase_index = self.phases.index(curr_phase)
        next_phase_index = (curr_phase_index + 1) % len(self.phases)
        return self.phases[next_phase_index]

    def schedule(self, inflow, curr_phase, curr_phase_duration, curr_time=0):

        Xempty = ScheduleStatus({phase: 0 for phase in self.phases})
        Xfull = ScheduleStatus({phase: len(sequence) for phase, sequence in inflow.items()})
        X = [Xempty]

        self.state_groups = {Xempty : {curr_phase : State(phase_duration=curr_phase_duration,
                                                          finish_time=curr_time,
                                                          delay=0,
                                                          previous_phase=None)}}
        self.start_times = {}

        cluster_count = Xfull.sum()

        for scheduled_count in range(cluster_count):
            
            Xcount = len(X)
            for x in range(Xcount):
                status = X.pop(0)
                for phase in self.phases:
                    updated_status = status.schedule(phase)
                    if Xfull[phase] >= updated_status[phase] and updated_status not in X:
                        X.append(updated_status)

            for status in X:
                for phase in self.phases:
                    if status[phase] > 0:
                        self.calculate_state_group(status,
                                                   phase,
                                                   inflow)

        # logger.debug('state_groups = {}'.format(self.state_groups))

        last_phase, best_leaf_state = self.get_minimum_delay_state(Xfull)

        # logger.debug('min_delay = {}'.format(best_leaf_state.delay))

        phase_sequence, phase_duration, start_times = self.backtrack(Xfull, last_phase)

        outflow = self.construct_outflow(inflow, phase_sequence, start_times)

        return outflow, phase_sequence, phase_duration

    def calculate_state_group(self, curr_status, curr_phase, inflow):
        next_cluster = inflow[curr_phase][curr_status[curr_phase]-1]
        previous_status = curr_status.unschedule(curr_phase)
        min_delay = float('inf')
        for previous_phase in self.phases:
            try:
                previous_state = self.state_groups[previous_status][previous_phase]
                new_state, cluster_start_time = self.update_state(previous_state,
                                                                  previous_phase,
                                                                  curr_phase,
                                                                  next_cluster)
                if new_state.finish_time < self.optimization_horizon and new_state.delay < min_delay:
                    if curr_status not in self.state_groups:
                        self.state_groups[curr_status] = {}
                        self.start_times[curr_status] = {}
                    self.state_groups[curr_status][curr_phase] = new_state
                    self.start_times[curr_status][curr_phase] = cluster_start_time
                    min_delay = new_state.delay
            except KeyError:
                pass

    def update_state(self, previous_state, previous_phase, curr_phase, next_cluster):
        phase_duration = previous_state.phase_duration
        curr_time = previous_state.finish_time
        delay = previous_state.delay

        if curr_phase != previous_phase and phase_duration < self.Gmin[previous_phase]:
            curr_time += self.Gmin[previous_phase] - phase_duration

        permitted_start_time = curr_time + self.min_switch(previous_phase, curr_phase)
        actual_start_time = max(next_cluster.arrival, permitted_start_time)

        if curr_phase != previous_phase and permitted_start_time > next_cluster.arrival:
            actual_start_time += self.startup_lost_time

        curr_time = actual_start_time + next_cluster.duration

        if curr_phase != previous_phase or (next_cluster.arrival - permitted_start_time > self.switch_back(curr_phase)):
            phase_duration = curr_time - permitted_start_time
        else:
            phase_duration += curr_time - permitted_start_time

        delay += next_cluster.count * (actual_start_time - next_cluster.arrival)

        return (State(phase_duration=phase_duration,
                      finish_time=curr_time,
                      delay=delay,
                      previous_phase=previous_phase),
                actual_start_time)

    def min_switch(self, previous_phase, curr_phase):
        return self._min_switch[previous_phase][curr_phase]

    def switch_back(self, phase):
        min_cycle = sum(self.Gmin.values()) + sum(self.Y.values())
        return min_cycle - self.Gmin[phase]

    def get_minimum_delay_state(self, Xfull):
        min_delay = float('inf')
        best_leaf_state = None
        last_phase = None
        for phase, state in self.state_groups[Xfull].items():
            if state.delay < min_delay:
                min_delay = state.delay
                last_phase = phase
                best_leaf_state = state
        return last_phase, best_leaf_state

    def backtrack(self, Xfull, last_phase):
        curr_state = self.state_groups[Xfull][last_phase]
        curr_phase = last_phase
        curr_status = Xfull
        phase_sequence = []
        phase_duration = []
        start_times = []
        while curr_state.previous_phase is not None:
            phase_sequence.insert(0, curr_phase)
            phase_duration.insert(0, curr_state.phase_duration)
            start_times.insert(0, self.start_times[curr_status][curr_phase])
            curr_status = curr_status.unschedule(curr_phase)
            curr_phase = curr_state.previous_phase
            curr_state = self.state_groups[curr_status][curr_phase]
        return phase_sequence, phase_duration, start_times

    def construct_outflow(self, inflow, phase_sequence, start_times):
        curr_cluster = ScheduleStatus({phase:0 for phase in inflow})
        outflow = ClusterSequence()
        for phase, start in zip(phase_sequence, start_times):
            next_cluster = inflow[phase][curr_cluster[phase]]
            outflow.append(Cluster(count=next_cluster.count,
                                   arrival=start,
                                   departure=start+next_cluster.duration))
            curr_cluster.schedule_in_place(phase)
        return outflow


class ScheduleStatus(object):
    def __init__(self, status=None):
        if status is None:
            status = {}
        self._status = status

    def __repr__(self):
        return '({})'.format(''.join(str(count) for count in self._status.values()))

    def __getitem__(self, phase):
        return self._status[phase]

    def __hash__(self):
        return hash(tuple(self._status.values()))

    def __len__(self):
        return len(self._status)

    def __eq__(self, other):
        result = True
        result = result and (type(self) == type(other))
        result = result and (len(self) == len(other))
        for phase in self._status.keys():
            result = result and (self[phase] == other[phase])
        return result

    def __ne__(self, other):
        return not self == other

    def sum(self):
        return sum(self._status.values())

    def schedule_in_place(self, phase):
        self._schedule(phase) 

    def schedule(self, phase):
        updated_status = self.copy()
        updated_status._schedule(phase)
        return updated_status

    def _schedule(self, phase):
        try:
            self._status[phase] += 1
        except KeyError:
            self._status[phase] = 1    

    def unschedule(self, phase):
        updated_status = self.copy()
        updated_status._unschedule(phase)
        return updated_status

    def _unschedule(self, phase):
        try:
            if self._status[phase] > 0:
                self._status[phase] -= 1
            else:
                logger.debug('No cluster to unschedule along phase {}'.format(phase))
        except KeyError:
            logger.debug('Phase {} not found in schedule status'.format(phase))
            raise

    def copy(self):
        return ScheduleStatus({phase:count for phase, count in self._status.items()})
