KILL = 0
RESP = 1
REQ = 2


class Message(object):
    def __init__(self, code):
        self.code = code


class Response(Message):
    def __init__(self, extension, decision_point):
        super(Response, self).__init__(RESP)
        self.extension = extension
        self.decision_point = decision_point


class Request(Message):
    def __init__(self, sensor_data, curr_phase, curr_phase_duration, curr_time):
        super(Request, self).__init__(REQ)
        self.curr_phase = curr_phase
        self.curr_phase_duration = curr_phase_duration
        self.curr_time = curr_time
        self.sensor_data = sensor_data


class KillPill(Message):
    def __init__(self):
        super(KillPill, self).__init__(KILL)
