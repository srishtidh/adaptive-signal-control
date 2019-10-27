import multiprocessing

import traci

import adasco.detector
import adasco.messaging

class Master(multiprocessing.Process):
    def __init__(self, port, registry):
        super(Master, self).__init__()
        self.connection = traci.connect(port=port)
        self.registry = registry
        self.detector = adasco.detector.ExactDetector(self.connection)
        
    def expects_more_vehicles(self):
        return self.connection.simulation.getMinExpectedNumber() > 0

    def update_all_phase_durations(self):
        map(self.update_phase_duration, self.registry)

    def update_phase_duration(self, entry):
        curr_phase = self.connection.trafficlights.getPhase(entry.agent.id)
        if curr_phase != entry.phase:
            entry.phase = curr_phase
            entry.phase_duration = 1
        else:
            entry.phase_duration += 1

    def extend_current_phase(self, traffic_light_id, extension):
        self.connection.trafficlights.setPhaseDuration(traffic_light_id, extension)

    def run(self):
        step = 0

        while self.expects_more_vehicles():
            self.connection.simulationStep()
            step += 1

            self.update_all_phase_durations()

            agents_at_decision_point = self.registry.get_agents_at_decision_point(step)

            for agent in agents_at_decision_point:

                sensor_data = self.detector.get_sensor_data(agent.agent.incoming_edges)

                request = adasco.messaging.Request(sensor_data=sensor_data,
                                                   curr_phase=agent.phase,
                                                   curr_phase_duration=agent.phase_duration,
                                                   curr_time=step)

                agent.request_queue.put(request)

            for agent in agents_at_decision_point:
                agent.request_queue.join()
                response = agent.response_queue.get()
                agent.decision_point = response.decision_point
                self.extend_current_phase(agent.agent.id, response.extension)

        self.connection.close()

        for agent in self.registry:
            agent.request_queue.put(adasco.messaging.KillPill())
        