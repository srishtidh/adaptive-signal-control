from __future__ import print_function
from __future__ import division

from collections import namedtuple
from math import ceil
import logging
import json

from docplex.cp.solver.solver_local import LocalSolverException
from docplex.cp.parameters import CpoParameters
import docplex.cp.model

from adasco.cluster import Cluster

logger = logging.getLogger(__name__)

SliceDeparture = namedtuple('SliceDeparture', ['departure', 'ratio'])


class CP(object):
    
    def __init__(self, phases, Gmin, Gmax, Y, sult, timelimit, cycle_count):
        self.phases = phases
        self.Gmin = Gmin
        self.Gmax = Gmax
        self.Y = Y

        self.sult = sult

        self.phase_count = len(phases)
        self.cycle_count = cycle_count
        
        self.threads = 1
        self.timelimit = timelimit * self.threads

        self.phase_intervals = {}
        self.cluster_intervals = {}

        self.model = None

    def schedule_over_all_samples(self, inflows, weights, curr_phase, curr_phase_duration, output_file=None, status_file=None):

        self.phase_intervals = {}
        self.cluster_intervals = {}

        self.model = docplex.cp.model.CpoModel()

        self.model.parameters = CpoParameters(LogVerbosity='Terse', Workers=self.threads,
                                         TimeLimit=self.timelimit, WarningLevel=0,
                                         TimeMode='CPUTime')

        self.create_phase_intervals(curr_phase, curr_phase_duration)

        for inflow_id, inflow in enumerate(inflows):
            self.create_cluster_intervals(inflow, inflow_id)

        self.constrain_phase_order()
        self.constrain_cycle_order()

        for inflow_id, inflow in enumerate(inflows):
            self.constrain_cluster_departure(inflow, inflow_id)
            self.constrain_cluster_precedence(inflow, inflow_id)

        self.add_objective(inflows, weights)

        if output_file is not None:
            self.model.export_model(output_file)

        try:
            solution = self.model.solve()
        except LocalSolverException:
            solution = None
            self.model.export_model('localsolverexception.cpo')
            print('LocalSolverException raised!')

        if solution:
            # TODO(srishti): Simplify it
            departures = []
            (delay,) = solution.get_objective_values()
            (gap,) = solution.get_objective_gaps()
            
            for inflow_id, inflow in enumerate(inflows):
                sample_departures = {}
                
                for phase, sequence in inflow.items():
                    if phase not in sample_departures:
                        sample_departures[phase] = []
                    
                    for cluster_id, cluster in enumerate(sequence):
                        cluster_departures = []
                        
                        for cycle in range(self.cycle_count):
                            var_sol = solution.get_var_solution(self.cluster_intervals[(inflow_id, phase, cluster_id, cycle)])
                            if var_sol.get_start() is not None and var_sol.get_size() > 0:
                                departure = SliceDeparture(departure=var_sol.get_start(),
                                                           ratio=var_sol.get_size()/cluster.duration)
                                cluster_departures.append(departure)
                        
                        sample_departures[phase].append(cluster_departures)

                departures.append(sample_departures)

            if status_file:
                with open(status_file, 'w') as fp:
                    json.dump({'status': solution.solve_status,
                               'delay': delay,
                               'gap': gap}, fp, indent=4)
            
            curr_phase_solution = solution.get_var_solution(self.phase_intervals[(curr_phase, 0)])
            curr_phase_end = curr_phase_solution.get_end()
            extension = curr_phase_end

        else:
            self.model.export_model('nosolution.cpo')
            print('No solution')
            extension = None
            departures = None

        return extension, departures

    def schedule_in_hindsight(self, inflow, curr_phase, curr_phase_duration, action, output_file=None, status_file=None):

        inflow_id = 0
        self.phase_intervals = {}
        self.cluster_intervals = {}

        self.model = docplex.cp.model.CpoModel()

        self.model.parameters = CpoParameters(LogVerbosity='Quiet', Workers=self.threads,
                                         TimeLimit=self.timelimit, WarningLevel=0,
                                         TimeMode='CPUTime')

        self.create_phase_intervals(curr_phase, curr_phase_duration, curr_phase_end=action)

        self.create_cluster_intervals(inflow)

        self.constrain_phase_order()
        self.constrain_cycle_order()

        self.constrain_cluster_departure(inflow)
        self.constrain_cluster_precedence(inflow)

        self.add_objective([inflow], [1])

        if output_file is not None:
            self.model.export_model(output_file)

        try:
            solution = self.model.solve()
        except LocalSolverException:
            solution = None
            self.model.export_model('localsolverexception.cpo')
            print('LocalSolverException raised!')

        if solution:
        
            departures = {}
            (delay,) = solution.get_objective_values()
            (gap,) = solution.get_objective_gaps()
            
            for phase, sequence in inflow.items():
                if phase not in departures:
                    departures[phase] = []
                for cluster_id, cluster in enumerate(sequence):
                    cluster_departures = []
                    for cycle in range(self.cycle_count):
                        var_sol = solution.get_var_solution(self.cluster_intervals[(inflow_id, phase, cluster_id, cycle)])
                        if var_sol.get_start() is not None and var_sol.get_size() > 0:
                            departure = SliceDeparture(departure=var_sol.get_start(),
                                                       ratio=var_sol.get_size()/cluster.duration)
                            cluster_departures.append(departure)
                    departures[phase].append(cluster_departures)
           
            if status_file:
                with open(status_file, 'w') as fp:
                    json.dump({'status': solution.solve_status,
                               'gap': gap}, fp, indent=4)

            curr_phase_solution = solution.get_var_solution(self.phase_intervals[(curr_phase, 0)])
            curr_phase_end = curr_phase_solution.get_end()
            extension = curr_phase_end

        else:
            self.model.export_model('nosolution.cpo')
            print('No solution')
            delay = None
            departures = None

        return extension, delay, cluster_departures

    def get_plan_for_sample(self, inflow, curr_phase, curr_phase_duration, output_file=None):

        inflow_id = 0
        self.phase_intervals = {}
        self.cluster_intervals = {}

        self.model = docplex.cp.model.CpoModel()

        self.model.parameters = CpoParameters(LogVerbosity='Quiet', Workers=self.threads,
                                         TimeLimit=self.timelimit, WarningLevel=0,
                                         TimeMode='CPUTime')

        self.create_phase_intervals(curr_phase, curr_phase_duration)

        self.create_cluster_intervals(inflow)

        self.constrain_phase_order()
        self.constrain_cycle_order()

        self.constrain_cluster_departure(inflow)
        self.constrain_cluster_precedence(inflow)

        self.add_objective([inflow], [1])

        if output_file is not None:
            self.model.export_model(output_file)

        try:
            solution = self.model.solve()
        except LocalSolverException:
            solution = None
            self.model.export_model('localsolverexception.cpo')
            print('LocalSolverException raised!')

        if solution:
            plan = {}

            for cycle in range(self.cycle_count):
                for phase in self.phases:
                    var_sol = solution.get_var_solution(self.phase_intervals[(phase, cycle)])
                    plan[(cycle, phase)] = (var_sol.get_start(), var_sol.get_end())

        else:
            self.model.export_model('nosolution.cpo')
            print('No solution')
            plan = None

        return plan    

    def schedule_inflow_according_to_plan(self, inflow, plan, output_file=None):

        inflow_id = 0
        self.phase_intervals = {}
        self.cluster_intervals = {}

        self.model = docplex.cp.model.CpoModel()

        self.model.parameters = CpoParameters(LogVerbosity='Quiet', Workers=self.threads,
                                         TimeLimit=self.timelimit, WarningLevel=0,
                                         TimeMode='CPUTime')

        self.initialize_phase_schedule(plan)

        self.create_cluster_intervals(inflow)

        self.constrain_phase_order()
        self.constrain_cycle_order()

        self.constrain_cluster_departure(inflow)
        self.constrain_cluster_precedence(inflow)

        self.add_objective([inflow], [1])

        if output_file is not None:
            self.model.export_model(output_file)

        try:
            solution = self.model.solve()
        except LocalSolverException:
            solution = None
            self.model.export_model('localsolverexception.cpo')
            print('LocalSolverException raised!')

        if solution:
            (delay,) = solution.get_objective_values()
        else:
            self.model.export_model('nosolution.cpo')
            print('No solution')
            delay = float('inf')

        return delay

    def add_objective(self, inflows, weights):

        delays = []

        for (inflow_id, phase, index, cycle), interval in self.cluster_intervals.items():
            cluster = inflows[inflow_id][phase][index]
            delay = self.model.start_of(interval, int(round(cluster.arrival))) - int(round(cluster.arrival))
            vehicle_count = cluster.count * self.model.size_of(interval, 0) / int(round(cluster.duration))
            sample_count = weights[inflow_id]
            delays.append(delay * vehicle_count * sample_count)

        self.model.add(self.model.minimize(self.model.sum(delays)))

    def create_phase_intervals(self, curr_phase, curr_phase_duration, curr_phase_end=None):

        max_cycle_length = sum([g for g in self.Gmax.values()]) + sum([y for y in self.Y.values()])
        max_plan_end_time = max_cycle_length * self.cycle_count
        plan_time_range = (-max_cycle_length, max_plan_end_time)

        for phase in self.phases:
            for cycle in range(self.cycle_count):
                start = -curr_phase_duration if (phase == curr_phase and cycle == 0) else plan_time_range
                end = plan_time_range if (phase < curr_phase and cycle == 0) else (0, max_plan_end_time)
                if (curr_phase_end is not None) and (phase == curr_phase) and (cycle == 0):
                    if curr_phase_end == 0:
                        end = 0
                    else:
                        end = (curr_phase_end, max_plan_end_time)
                self.phase_intervals[(phase, cycle)] = self.model.interval_var(start=start,
                                                                          end=end,
                                                                          size=(self.Gmin[phase], self.Gmax[phase]),
                                                                          name='P{}-{}'.format(phase, cycle))

    def create_cluster_intervals(self, inflow, inflow_id=0):

        max_cycle_length = sum([g for g in self.Gmax.values()]) + sum([y for y in self.Y.values()])
        max_plan_end_time = max_cycle_length * self.cycle_count
 
        for phase, sequence in inflow.items():
            for index, cluster in enumerate(sequence):
                for cycle in range(self.cycle_count):
                    self.cluster_intervals[(inflow_id, phase, index, cycle)] = self.model.interval_var(start=(int(cluster.arrival), max_plan_end_time),
                                                                                                  end=(int(cluster.arrival), max_plan_end_time),
                                                                                                  size=(1, int(round(cluster.duration))),
                                                                                                  optional=True,
                                                                                                  name='C{}-{}-{}-{}'.format(inflow_id, phase, index, cycle))

    def initialize_phase_schedule(self, plan):

        for phase in self.phases:
            for cycle in range(self.cycle_count):
                start, end = plan[(cycle, phase)]
                self.phase_intervals[(phase, cycle)] = self.model.interval_var(start=start,
                                                                          end=end,
                                                                          name='P{}-{}'.format(phase, cycle))


    def constrain_phase_order(self):
        for index, phase in enumerate(self.phases):
            if index == 0:
                continue
            prev_phase = self.phases[index-1]
            for cycle in range(self.cycle_count):
                self.model.add(self.model.end_at_start(self.phase_intervals[(prev_phase, cycle)],
                                                     self.phase_intervals[(phase, cycle)],
                                                     delay=self.Y[prev_phase]))

    def constrain_cycle_order(self):
        first_phase = self.phases[0]
        last_phase = self.phases[-1]
        for cycle in range(1, self.cycle_count):
            self.model.add(self.model.end_at_start(self.phase_intervals[(last_phase, cycle-1)],
                                                 self.phase_intervals[(first_phase, cycle)],
                                                 delay=self.Y[last_phase]))

    def constrain_cluster_precedence(self, inflow, inflow_id=0):

        # Presence
        for phase, sequence in inflow.items():
            for index, cluster in enumerate(sequence):
                if index == 0:
                    continue
                for cycle in range(self.cycle_count):
                    self.model.add(self.model.end_before_start(self.cluster_intervals[(inflow_id, phase, index-1, cycle)],
                                                               self.cluster_intervals[(inflow_id, phase, index, cycle)]))

                    for future_cycle in range(cycle+1, self.cycle_count):
                        self.model.add(self.model.if_then(self.model.presence_of(self.cluster_intervals[(inflow_id, phase, index, cycle)]),
                                                          self.model.logical_not(self.model.presence_of(self.cluster_intervals[(inflow_id, phase, index-1, future_cycle)]))))

    def constrain_cluster_departure(self, inflow, inflow_id=0):
        for phase, sequence in inflow.items():
            for index, cluster in enumerate(sequence):
                for cycle in range(self.cycle_count):
                    self.model.add(self.model.start_before_start(self.phase_intervals[(phase, cycle)],
                                                       self.cluster_intervals[(inflow_id, phase, index, cycle)]))
                    self.model.add(self.model.end_before_end(self.cluster_intervals[(inflow_id, phase, index, cycle)],
                                                   self.phase_intervals[(phase, cycle)]))

                self.model.add(self.model.sum([self.model.size_of(self.cluster_intervals[(inflow_id, phase, index, cycle)]) for cycle in range(self.cycle_count)]) == int(round(cluster.duration)))