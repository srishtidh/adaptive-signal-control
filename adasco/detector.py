from __future__ import print_function
from __future__ import division

import logging

logger = logging.getLogger(__name__)


class SensorData(object):

    def __init__(self, queue_length, queued_vehicle_positions, queued_vehicle_ids,
                 arriving_vehicle_positions, arriving_vehicle_ids):
        self.queue_length = queue_length
        self.queued_vehicle_positions = queued_vehicle_positions
        self.queued_vehicle_ids = queued_vehicle_ids
        self.arriving_vehicle_positions = arriving_vehicle_positions
        self.arriving_vehicle_ids = arriving_vehicle_ids

    def __repr__(self):
        return '{}(queue_length={}, queued_vehicle_positions={}, arriving_vehicle_positions={})'.format(self.__class__.__name__,
                                                                                                        self.queue_length,
                                                                                                        self.queued_vehicle_positions,
                                                                                                        self.arriving_vehicle_positions)

class ExactDetector(object):

    def __init__(self, connection, observation_horizon=float('inf')):
        assert connection is not None
        self.connection = connection
        self.observation_horizon = observation_horizon

    def get_vehicle_positions(self, laneID):
        queued_vehicle_positions = []
        queued_vehicle_ids = []
        arriving_vehicle_positions = []
        arriving_vehicle_ids = []

        lane_length = self.connection.lane.getLength(laneID)
        vehicles = self.connection.lane.getLastStepVehicleIDs(laneID)

        for vehID in vehicles:
            vehicle_position = self.connection.vehicle.getLanePosition(vehID)
            distance_to_junction = lane_length - vehicle_position

            if distance_to_junction > self.observation_horizon:
                continue

            vehicle_speed = self.connection.vehicle.getSpeed(vehID)

            if vehicle_speed >= 0.1:
                arriving_vehicle_positions.append(distance_to_junction)
                arriving_vehicle_ids.append(vehID)
            else:
                queued_vehicle_positions.append(distance_to_junction)
                queued_vehicle_ids.append(vehID)

        return (queued_vehicle_positions, queued_vehicle_ids, 
                arriving_vehicle_positions, arriving_vehicle_ids)

    def get_sensor_data(self, edges):
        data = {}

        for edge, lanes in edges.items():

            edge_queue_length = 0
            edge_queued_vehicle_positions = []
            edge_queued_vehicle_ids = []
            edge_arriving_vehicle_positions = []
            edge_arriving_vehicle_ids = []

            for lane in lanes:
                (lane_queued_positions, lane_queued_vehicle_ids, lane_arriving_positions,
                 lane_arriving_vehicle_ids) = self.get_vehicle_positions(lane)
                edge_queue_length += len(lane_queued_vehicle_ids)
                edge_queued_vehicle_positions.extend(lane_queued_positions)
                edge_queued_vehicle_ids.extend(lane_queued_vehicle_ids)
                edge_arriving_vehicle_positions.extend(lane_arriving_positions)
                edge_arriving_vehicle_ids.extend(lane_arriving_vehicle_ids)

            data[edge] = SensorData(edge_queue_length,
                                    edge_queued_vehicle_positions,
                                    edge_queued_vehicle_ids,
                                    edge_arriving_vehicle_positions,
                                    edge_arriving_vehicle_ids)

        return data
        