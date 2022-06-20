""" This is the implementation of the Software-Defined Wireless Sensor Network
environment """
import imp
import random
# from scipy import rand
from random import randrange
import networkx as nx
import gym
from gym import spaces
import numpy as np
import json
from time import sleep
from datetime import datetime

from sdwsn_common import common
from sdwsn_tsch.schedule import Schedule
from sdwsn_routes.routes import Routes
from sdwsn_database.database import NODES_INFO
from sdwsn_tsch.contention_free_scheduler import contention_free_schedule
from sdwsn_database.database import OBSERVATIONS

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27


class Env(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, packet_dissector, network_reconfiguration, max_channel_offsets=3, max_slotframe_size=100):
        super(Env, self).__init__()
        self.packet_dissector = packet_dissector
        self.nc = network_reconfiguration
        self.max_channel_offsets = max_channel_offsets
        self.max_slotframe_size = max_slotframe_size
        # Keep track of the running routes
        self.routes = Routes()
        # Keep track of schedules
        self.schedule = Schedule(
            self.max_slotframe_size, max_channel_offsets)
        # We define the number of actions
        n_actions = 2  # increase and decrease slotframe size
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the user requirements, last ts, SF size and normalized ts in schedule
        self.n_observations = 6
        self.observation_space = spaces.Box(low=0, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    """ Reset the environment, reset the routing and the TSCH schedules """

    def reset(self):
        # We get the network links, useful when calculating the routing
        G = common.get_network_links(self.packet_dissector)
        # Run the chosen algorithm with the current links
        path = common.compute_algo(G, "dijkstra", self.routes)
        # Set the slotframe size
        slotframe_size = 23
        # We now set the TSCH schedules for the current routing
        contention_free_schedule(self.schedule, path, slotframe_size)
        # We now set and save the user requirements
        select_user_req = [0.8, 0.1, 0.1]
        # Let's prepare the schedule information in the json format
        schedules_json = self.schedule.schedule_toJSON(slotframe_size)
        print("json")
        print(json.dumps(schedules_json, indent=4, sort_keys=True))
        while len(schedules_json['cells']) > 12:
            print("fragmentation is required for TSCH schedule job")
            extra_cells = schedules_json['cells'][12:]
            del schedules_json['cells'][12:]
            new_job = json.dumps(schedules_json, indent=4, sort_keys=True)
            # set job id
            self.packet_dissector.sequence += 1
            # Send job with id and wait for reply
            self.send_job(new_job, self.packet_dissector.sequence)
            del schedules_json['cells']
            schedules_json['cells'] = extra_cells
            schedules_json["sf_len"] = 0

        schedules_json = json.dumps(schedules_json, indent=4, sort_keys=True)
        # Let's prepare the routing information in the json format
        routes_json = self.routes.routes_toJSON()
        # set job id
        self.packet_dissector.sequence += 1
        # Send job with id and wait for reply
        self.send_job(schedules_json, self.packet_dissector.sequence)
        # set job id
        self.packet_dissector.sequence += 1
        # Send job with id and wait for reply
        self.send_job(routes_json, self.packet_dissector.sequence)
        # Wait for the network to settle
        sleep(0.5)
        # We now save all the observations
        # They are of the form "time, user requirements, routing matrix, schedules matrix, sf len"
        sample_time = datetime.now().timestamp() * 1000.0
        # We now save the user requirements
        user_requirements = np.array(select_user_req)
        # We now build the TSCH schedule matrix
        _, last_ts = common.build_link_schedules_matrix_obs(
            self.packet_dissector, self.schedule)
        ts_in_schedule = self.schedule.get_list_ts_in_use()
        sum = 0
        for ts in ts_in_schedule:
            sum += 2**ts
        normalized_ts_in_schedule = sum/(2**slotframe_size)
        # We now save the observations with reward None
        # observation = np.zeros(self.n_observations).astype(np.float32)
        # slotframe_size = slotframe_size + 15
        observation = np.append(user_requirements, last_ts)
        observation = np.append(observation, slotframe_size)
        observation = np.append(observation, normalized_ts_in_schedule)
        self.save_observations(
            sample_time, select_user_req[0], select_user_req[1], select_user_req[2],
            None, None, None,
            None, None, None,
            None, None,
            last_ts, slotframe_size, normalized_ts_in_schedule,
            None)
        return observation  # reward, done, info can't be included

    # Send to the SDWSN
    def send_job(self, data, job_id):
        # Send the job to the NC process
        result = self.nc.send_nc(data, job_id)
        if result == 0:
            print("job did not completed")

    """ Save observations """

    def save_observations(self, timestamp, alpha, beta, delta,
                          power_wam, power_mean, power_normalized,
                          delay_wam, delay_mean, delay_normalized,
                          pdr_wam, pdr_mean,
                          last_ts_in_schedule, current_sf_len, normalized_ts_in_schedule,
                          reward):
        data = {
            "timestamp": timestamp,
            "alpha": alpha,
            "beta": beta,
            "delta": delta,
            "power_wam": power_wam,
            "power_avg": power_mean,
            "power_normalized": power_normalized,
            "delay_wam": delay_wam,
            "delay_avg": delay_mean,
            "delay_normalized": delay_normalized,
            "pdr_wam": pdr_wam,
            "pdr_mean": pdr_mean,
            "last_ts_in_schedule": last_ts_in_schedule,
            "current_sf_len": current_sf_len,
            "normalized_ts_in_schedule": normalized_ts_in_schedule,
            "reward": reward
        }
        self.packet_dissector.db.insert(OBSERVATIONS, data)
