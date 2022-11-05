#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

""" This is the implementation of the Software-Defined Wireless Sensor Network
environment """
import gym
from gym import spaces
import numpy as np
from time import sleep
from datetime import datetime
import random
from random import randrange

from sdwsn_controller.common import common
from sdwsn_controller.result_analysis.run_analysis import run_analysis

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27

MAX_SLOTFRAME_SIZE = 70


class Env(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(
            self,
            simulation_name: str,
            controller: object,
            folder: str = './figures/'
    ):
        super(Env, self).__init__()
        self.controller = controller
        self.folder = folder
        self.simulation_name = simulation_name
        # We define the number of actions
        n_actions = 3  # increase and decrease slotframe size
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the user requirements, power, delay, pdr, last ts active in schedule, and current slotframe size
        self.n_observations = 8
        self.observation_space = spaces.Box(low=0, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    """ Step action """

    def step(self, action):
        sample_time = datetime.now().timestamp() * 1000.0
        # We now get the last observations
        obs = self.controller.get_state()
        if action == 0:
            # print("increasing slotframe size")
            sf_len = common.next_coprime(obs['current_sf_len'])
        if action == 1:
            # print("decreasing slotframe size")
            sf_len = common.previous_coprime(obs['current_sf_len'])
        if action == 2:
            sf_len = obs['current_sf_len']
        # Send the entire TSCH schedule
        self.controller.send_tsch_schedules()
        # Delete the current nodes_info collection from the database
        self.controller.delete_info_collection()
        # Reset sequence
        self.controller.reset_pkt_sequence()
        # We now wait until we reach the processing_window
        while (not self.controller.wait()):
            print("resending schedules")
            self.controller.send_tsch_schedules()
            # Delete the current nodes_info collection from the database
            self.controller.delete_info_collection()
            # Reset sequence
            self.controller.reset_pkt_sequence()
        # print("process reward")
        # TODO: DO we really need this delay?
        self.controller.processing_wait(1)
        # Calculate the reward
        reward, cycle_power, cycle_delay, cycle_pdr = self.controller.calculate_reward(
            self.controller.alpha, self.controller.beta, self.controller.delta, sf_len)
        # Append to the observations
        sample_time = datetime.now().timestamp() * 1000.0
        observation = np.append(obs['user_requirements'], cycle_power[2])
        observation = np.append(observation, cycle_delay[2])
        observation = np.append(observation, cycle_pdr[1])
        observation = np.append(
            observation, obs['last_ts_in_schedule']/MAX_SLOTFRAME_SIZE)
        observation = np.append(observation, sf_len/MAX_SLOTFRAME_SIZE)
        self.controller.save_observations(
            timestamp=sample_time,
            alpha=self.controller.alpha,
            beta=self.controller.beta,
            delta=self.controller.delta,
            power_wam=cycle_power[0],
            power_mean=cycle_power[1],
            power_normalized=cycle_power[2],
            delay_wam=cycle_delay[0],
            delay_mean=cycle_delay[1],
            delay_normalized=cycle_delay[2],
            pdr_wam=cycle_pdr[0],
            pdr_mean=cycle_pdr[1],
            current_sf_len=sf_len,
            last_ts_in_schedule=obs['last_ts_in_schedule'],
            reward=reward
        )
        done = False
        info = {}
        # MAX_SLOTFRAME_SIZE is the maximum slotframe size
        # TODO: Set the maximum slotframe size at the creation
        # of the environment
        if (sf_len < obs['last_ts_in_schedule'] or sf_len > MAX_SLOTFRAME_SIZE):
            done = True
            reward = -4

        return observation, reward, done, info

    """ Reset the environment, reset the routing and the TSCH schedules """

    def reset(self):
        # Reset the container controller
        self.controller.reset()
        # We now wait until we reach the processing_window
        self.controller.wait()
        # We get the network links, useful when calculating the routing
        G = self.controller.get_network_links()
        # Run the dijkstra algorithm with the current links
        path = self.controller.compute_routes(G)
        # Lets set the type of scheduler
        # types_scheduler = ['Contention Free', 'Unique Schedule']
        # type_scheduler = random.choice(types_scheduler)
        # self.controller.scheduler = type_scheduler
        # self.controller.scheduler = 'Unique Schedule'
        # Set the slotframe size
        slotframe_size = 15
        # We now set the TSCH schedules for the current routing
        self.controller.compute_tsch_schedule(path, slotframe_size)
        # We now set and save the user requirements
        balanced = (0.4, 0.3, 0.3)
        energy = (0.8, 0.1, 0.1)
        delay = (0.1, 0.8, 0.1)
        reliability = (0.1, 0.1, 0.8)
        user_req = [balanced, energy, delay, reliability]
        select_user_req = random.choice(user_req)
        self.controller.user_requirements = select_user_req
        # Send the entire routes
        self.controller.send_routes()
        # Send the entire TSCH schedule
        self.controller.send_tsch_schedules()
        # Delete the current nodes_info collection from the database
        self.controller.delete_info_collection()
        self.controller.reset_pkt_sequence()
        # Wait for the network to settle
        self.controller.wait()
        # We now save all the observations
        # This is done for the numerical environment.
        self.controller.last_tsch_link = randrange(9+1, 20)
        # Get last active ts
        last_ts_in_schedule = self.controller.last_tsch_link
        # Set the slotframe size
        slotframe_size = last_ts_in_schedule
        # slotframe_size = last_ts_in_schedule
        # They are of the form "time, user requirements, routing matrix, schedules matrix, sf len"
        sample_time = datetime.now().timestamp() * 1000.0
        # We now save the user requirements
        user_requirements = self.controller.user_requirements
        # We now save the observations with reward None
        _, cycle_power, cycle_delay, cycle_pdr = self.controller.calculate_reward(
            self.controller.alpha, self.controller.beta, self.controller.delta, slotframe_size)
       # Append to the observations
        sample_time = datetime.now().timestamp() * 1000.0
        observation = np.append(user_requirements, cycle_power[2])
        observation = np.append(observation, cycle_delay[2])
        observation = np.append(observation, cycle_pdr[1])
        observation = np.append(
            observation, last_ts_in_schedule/MAX_SLOTFRAME_SIZE)
        observation = np.append(observation, slotframe_size/MAX_SLOTFRAME_SIZE)
        self.controller.save_observations(
            timestamp=sample_time,
            alpha=self.controller.alpha,
            beta=self.controller.beta,
            delta=self.controller.delta,
            power_wam=cycle_power[0],
            power_mean=cycle_power[1],
            power_normalized=cycle_power[2],
            delay_wam=cycle_delay[0],
            delay_mean=cycle_delay[1],
            delay_normalized=cycle_delay[2],
            pdr_wam=cycle_pdr[0],
            pdr_mean=cycle_pdr[1],
            current_sf_len=slotframe_size,
            last_ts_in_schedule=last_ts_in_schedule,
            reward=None
        )
        return observation  # reward, done, info can't be included

    def render(self, mode='console'):
        print(f"mode: {mode}")
        # if mode != 'console':
        #     raise NotImplementedError()
        # agent is represented as a cross, rest as a dot
        print('rendering')
        number = random.randint(0, 100)
        run_analysis(self.controller.db,
                     self.simulation_name+str(number), self.folder, True)

    def close(self):
        """ 
        Here, we want to export the observation collections to CSV format

        """
        self.controller.export_db(self.simulation_name, self.folder)
        pass
