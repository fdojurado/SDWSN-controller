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
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from random import randrange

from sdwsn_controller.common import common

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27


class Env(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(
            self,
            # simulation_name: str,
            controller: object,
            max_slotframe_size: None,
            # folder: str = './figures/'
    ):
        super(Env, self).__init__()
        # assert isinstance(simulation_name, str)
        # assert isinstance(folder, str)
        self.controller = controller

        assert isinstance(max_slotframe_size, int)
        self.max_slotframe_size = max_slotframe_size
        # self.folder = folder
        # self.simulation_name = simulation_name
        # We define the number of actions
        n_actions = 3  # increase and decrease slotframe size
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the user requirements, power, delay, pdr, last ts active in schedule, and current slotframe size
        self.n_observations = 8
        self.observation_space = spaces.Box(low=-1, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    """ Step action """

    def step(self, action):
        # We now get the last observations
        state = self.controller.get_state()
        if action == 0:
            # print("increasing slotframe size")
            sf_len = common.next_coprime(state['current_sf_len'])
        if action == 1:
            # print("decreasing slotframe size")
            sf_len = common.previous_coprime(state['current_sf_len'])
        if action == 2:
            # print("same slotframe size")
            sf_len = state['current_sf_len']
        # Set the SF size
        self.controller.current_slotframe_size = sf_len
        # Send the entire TSCH schedule
        self.controller.send_tsch_schedules()
        # We now wait until we reach the processing_window
        while (not self.controller.wait()):
            print("resending schedules")
            self.controller.send_tsch_schedules()
        observation, info = self._get_obs()
        done = False
        reward = info['reward']
        # self.max_slotframe_size is the maximum slotframe size
        # TODO: Set the maximum slotframe size at the creation
        # of the environment
        if (sf_len < state['last_ts_in_schedule'] or
                sf_len > self.max_slotframe_size):
            done = True
            reward = -4

        return observation, reward, done, False, info

    def _get_obs(self):
        state = self.controller.get_state()
        metrics = self.controller.calculate_reward(
            self.controller.alpha, self.controller.beta, self.controller.delta,
            state['current_sf_len'])
        # Append to the observations
        user_requirements = np.array(
            state['user_requirements'], dtype=np.float32)
        power_normalized = np.array(
            metrics['power_normalized'], dtype=np.float32)
        observation = np.append(user_requirements, power_normalized)
        delay_normalized = np.array(
            metrics['delay_normalized'], dtype=np.float32)
        observation = np.append(observation, delay_normalized)
        pdr_mean = np.array(metrics['pdr_mean'], dtype=np.float32)
        observation = np.append(observation, pdr_mean)
        last_ts_in_schedule = np.array(
            state['last_ts_in_schedule']/self.max_slotframe_size, dtype=np.float32)
        observation = np.append(
            observation, last_ts_in_schedule)
        slotframe_size = np.array(
            state['current_sf_len']/self.max_slotframe_size, dtype=np.float32)
        observation = np.append(
            observation, slotframe_size)
        return observation, metrics

    """ Reset the environment, reset the routing and the TSCH schedules """

    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)
        # Reset the container controller
        self.controller.reset()
        # We now wait until we reach the processing_window
        self.controller.wait()
        # We get the network links, useful when calculating the routing
        G = self.controller.get_network_links()
        # Run the dijkstra algorithm with the current links
        path = self.controller.compute_routes(G)
        # Set the initial SF size, this has to be greater that the # sensors
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
        # Wait for the network to settle
        self.controller.wait()
        # We now save all the observations
        # This is done for the numerical environment.
        self.controller.last_tsch_link = randrange(9+1, 20)
        # Get last active ts
        last_ts_in_schedule = self.controller.last_tsch_link
        # Set a random initial slotframe size
        slotframe_size = random.randint(
            last_ts_in_schedule+5, self.max_slotframe_size-5)
        # slotframe_size = last_ts_in_schedule
        self.controller.current_slotframe_size = slotframe_size
        # We now save the user requirements
        observation, info = self._get_obs()
        return observation, info  # reward, done, info can't be included

    def render(self, mode='console'):
        pass

    def close(self):
        pass
