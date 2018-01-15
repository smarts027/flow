import random

import numpy as np
import logging

class BaseLaneChangeController:
    """
    Base Class for Lane Change controllers.
    """

    def __init__(self, vehId):
        self.SumoController = False
        self.veh_id = vehId

    def isSumoController(self):
        return self.SumoController

    def get_action(self, env):
        return None


class SumoLaneChangeController(BaseLaneChangeController):
    def __init__(self, veh_id):
        super().__init__(veh_id)
        self.SumoController = True

class StaticLaneChanger(BaseLaneChangeController):
    """
    A lane-changing model used to perpetually keep a vehicle in the same
    lane.

    Attributes
    ----------
    veh_id: str
        unique vehicle identifier
    """


    def get_action(self, env):
        return env.vehicles.get_lane(self.veh_id)

class StochasticLaneChanger(BaseLaneChangeController):
    def __init__(self, veh_id, speedThreshold=5, prob=0.5, dxBack=0,
                 dxForward=60, gapBack=10, gapForward=5):
        super().__init__(veh_id)
        self.speedThreshold = speedThreshold
        self.prob = prob
        self.dxBack = dxBack
        self.dxForward = dxForward
        self.gapBack = gapBack
        self.gapForward = gapForward

    def get_action(self, env):
        """
        Determines optimal lane

        Parameters
        ----------
        env: Environment type
            environment variable (see flow/envs/base_env.py)

        :return: controller specified velocity for specific car
        """
        num_lanes = env.scenario.lanes
        v = [0] * env.scenario.lanes
        for lane in range(num_lanes):
            # count the cars in this lane
            leadID = env.vehicles.get_leader(self.veh_id)
            trailID = env.vehicles.get_follower(self.veh_id)

            if not leadID or not trailID:
                # empty lanes are assigned maximum speeds
                v[lane] = env.vehicles.get_state(self.veh_id, 'max_speed')
                continue

            leadPos = env.get_x_by_id(leadID)
            trailPos = env.get_x_by_id(trailID)

            thisPos = env.get_x_by_id(self.veh_id)

            headway = (leadPos - thisPos) % env.scenario.length  # d_l
            footway = (thisPos - trailPos) % env.scenario.length  # d_f

            if headway < self.gapForward or footway < self.gapBack:
                # if cars are too close together, set lane velocity to 0
                v[lane] = 0
                continue

            # otherwise set v[lane] to the mean velocity of all cars in the
            # region
            other_car_ids = env.get_cars(self.veh_id, dxBack=self.dxBack,
                                         dxForward=self.dxForward, lane=lane)
            v[lane] = np.mean([env.vehicles.get_speed(other_id)
                               for other_id in other_car_ids])

        maxv = max(v)  # determine max velocity
        maxl = v.index(maxv)  # lane with max velocity
        # speed of lane where car with specified self.veh_id is located
        myv = v[env.vehicles.get_lane(self.veh_id)]

        # choosing preferred lane:
        # new lane is chosen with a probability prob
        # if its velocity is sufficiently greater than that of the current lane
        if maxl != env.vehicles[self.veh_id]['lane'] and \
                        (maxv - myv) > self.speedThreshold and \
                        random.random() < self.prob:
            return maxl
        return env.vehicles[self.veh_id]['lane']


class StochasticLaneChanger(BaseLaneChangeController):
    def __init__(self, veh_id, speedThreshold=5, prob=0.5, dxBack=0,
                 dxForward=60, gapBack=10, gapForward=5):
        super().__init__(veh_id)
        self.speedThreshold = speedThreshold
        self.prob = prob
        self.dxBack = dxBack
        self.dxForward = dxForward
        self.gapBack = gapBack
        self.gapForward = gapForward

    def get_action(self, env):
        """
        Determines optimal lane

        Parameters
        ----------
        env: Environment type
            environment variable (see flow/envs/base_env.py)

        :return: controller specified velocity for specific car
        """
        num_lanes = env.scenario.lanes
        v = [0] * env.scenario.lanes
        for lane in range(num_lanes):
            # count the cars in this lane
            leadID = env.vehicles.get_leader(self.veh_id)
            trailID = env.vehicles.get_follower(self.veh_id)

            if not leadID or not trailID:
                # empty lanes are assigned maximum speeds
                v[lane] = env.vehicles.get_state(self.veh_id, 'max_speed')
                continue

            leadPos = env.get_x_by_id(leadID)
            trailPos = env.get_x_by_id(trailID)

            thisPos = env.get_x_by_id(self.veh_id)

            headway = (leadPos - thisPos) % env.scenario.length  # d_l
            footway = (thisPos - trailPos) % env.scenario.length  # d_f

            if headway < self.gapForward or footway < self.gapBack:
                # if cars are too close together, set lane velocity to 0
                v[lane] = 0
                continue

            # otherwise set v[lane] to the mean velocity of all cars in the
            # region
            other_car_ids = env.get_cars(self.veh_id, dxBack=self.dxBack,
                                         dxForward=self.dxForward, lane=lane)
            v[lane] = np.mean([env.vehicles.get_speed(other_id)
                               for other_id in other_car_ids])

        maxv = max(v)  # determine max velocity
        maxl = v.index(maxv)  # lane with max velocity
        # speed of lane where car with specified self.veh_id is located
        myv = v[env.vehicles.get_lane(self.veh_id)]

        # choosing preferred lane:
        # new lane is chosen with a probability prob
        # if its velocity is sufficiently greater than that of the current lane
        if maxl != env.vehicles[self.veh_id]['lane'] and \
                        (maxv - myv) > self.speedThreshold and \
                        random.random() < self.prob:
            return maxl
        return env.vehicles[self.veh_id]['lane']


class AggressiveLaneChanger(BaseLaneChangeController):
    def __init__(self, veh_id, target_velocity, threshold=0.75):
        """
        A lane-changing model used to perpetually keep a vehicle in the same
        lane.

        Attributes
        ----------
        veh_id: str
            unique vehicle identifier
        """
        super().__init__(veh_id)
        self.veh_id = veh_id
        self.threshold_velocity = target_velocity * threshold

    def get_action(self, env):
        if env.vehicles.get_speed(self.veh_id) < self.threshold_velocity:
            headways, reverse_headways = env.get_leader_blocker_headways(self.veh_id)
            desired_lane = np.argmax(headways)
            # print(desired_lane)
            if reverse_headways[desired_lane] < 5:
                # print("blocked!")
                return env.vehicles.get_lane(self.veh_id)
            else:
                return desired_lane
            # curr_lane = env.vehicles.get_lane(self.veh_id)
            # available_lanes = list(range(max(curr_lane-1,0), min(curr_lane + 1, env.scenario.lanes) +1))
            # headways = env.get_leader_headways(self.veh_id)[max(curr_lane-1,0): min(curr_lane + 1, env.scenario.lanes) +1]
            # desired_available_lane = np.argmax(headways)
            # desired_lane = available_lanes[desired_available_lane]

        else:
            return env.vehicles.get_lane(self.veh_id)

class SafeAggressiveLaneChanger(BaseLaneChangeController):
    def __init__(self, veh_id, target_velocity, threshold=0.75):
        """
        A lane-changing model used to perpetually keep a vehicle in the same
        lane.

        Attributes
        ----------
        veh_id: str
            unique vehicle identifier
        """
        super().__init__(veh_id)
        self.veh_id = veh_id
        self.threshold_velocity = target_velocity * threshold

    def get_action(self, env):
        if env.vehicles.get_speed(self.veh_id) < self.threshold_velocity:
            headways, reverse_headways = env.get_leader_blocker_headways(self.veh_id)
            curr_lane = env.vehicles.get_lane(self.veh_id)

            available_lanes = list(range(max(curr_lane-1,0), min(curr_lane + 1, env.scenario.lanes) +1))
            available_headways = headways[max(curr_lane-1,0): min(curr_lane + 1, env.scenario.lanes) +1]
            desired_available_lane = np.argmax(available_headways)
            desired_lane = available_lanes[desired_available_lane]
            if reverse_headways[desired_lane] < 8:
                # print("blocked!")
                return env.vehicles.get_lane(self.veh_id)
            else:
                return desired_lane
        else:
            return env.vehicles.get_lane(self.veh_id)


def stochastic_lane_changer(speedThreshold=5, prob=0.5,
                            dxBack=0, dxForward=60,
                            gapBack=10, gapForward=5):
    """
    Intelligent lane changer
    :param speedThreshold: minimum speed increase required
    :param prob: probability change will be requested if
           warranted = this * speedFactor
    :param dxBack: Farthest distance back car can see
    :param dxForward: Farthest distance forward car can see
    :param gapBack: Minimum required clearance behind car
    :param gapForward: Minimum required clearance in front car
    :return: carFn to input to a carParams
    """

    def controller(carID, env):
        """
        Determines optimal lane
        :param carID: id of the vehicle of interest
        :param env: environment variable
        :return: controller specified velocity for specific car
        """
        num_lanes = env.scenario.lanes
        v = [0] * env.scenario.lanes
        for lane in range(num_lanes):
            # count the cars in this lane
            leadID = env.get_leading_car(carID, lane)
            trailID = env.get_trailing_car(carID, lane)

            if not leadID or not trailID:
                # empty lanes are assigned maximum speeds
                v[lane] = env.vehicles[carID]['max_speed']
                continue

            leadPos = env.get_x_by_id(leadID)
            trailPos = env.get_x_by_id(trailID)

            thisPos = env.get_x_by_id(carID)

            headway = (leadPos - thisPos) % env.scenario.length  # d_l
            footway = (thisPos - trailPos) % env.scenario.length  # d_f

            if headway < gapForward or footway < gapBack:
                # if cars are too close together, set lane velocity to 0
                v[lane] = 0
                continue

            # otherwise set v[lane] to the mean velocity of all cars in the
            # region
            other_car_ids = env.get_cars(carID, dxBack=dxBack,
                                         dxForward=dxForward, lane=lane)
            v[lane] = np.mean([env.vehicles.get_speed(other_id)
                               for other_id in other_car_ids])

        maxv = max(v)  # determine max velocity
        maxl = v.index(maxv)  # lane with max velocity
        # speed of lane where car with specified carID is located
        myv = v[env.vehicles.get_lane(carID)]

        # choosing preferred lane:
        # new lane is chosen with a probability prob
        # if its velocity is sufficiently greater than that of the current lane
        if maxl != env.vehicles.get_lane(carID) and \
                        (maxv - myv) > speedThreshold and \
                        random.random() < prob:
            return maxl
        return env.vehicles.get_lane(carID)

    return controller