class Entry(object):
    def __init__(self, process, request_queue, response_queue, curr_phase,
                 curr_phase_duration, decision_point):
        self.agent = process
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.phase = curr_phase
        self.phase_duration = curr_phase_duration
        self.decision_point = decision_point

    def __repr__(self):
        return '{}(ID={}, phase={}, phase_duration={}, decision_point={})'.format(self.__class__.__name__,
                                                                                  self.agent.id,
                                                                                  self.phase,
                                                                                  self.phase_duration,
                                                                                  self.decision_point)


class Registry(object):
    def __init__(self):
        self.registry = []

    def __iter__(self):
        return iter(self.registry)

    def __len__(self):
        return len(self.registry)

    def __getitem__(self, index):
        return self.registry[index]

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.registry)

    def __bool__(self):
        return len(self) > 0

    def append(self, entry):
        self.registry.append(entry)

    def get_agents_at_decision_point(self, time):
        return [entry for entry in self.registry if entry.decision_point == time]
