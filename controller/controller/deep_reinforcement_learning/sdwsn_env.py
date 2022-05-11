""" This is the implemantion of the Software-Defined Wireless Sensor Network
environment """

import gym
from gym import spaces
import numpy as np


class sdwsnEnv(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, num_nodes, max_channel_offsets, max_slotframe_size):
        super(sdwsnEnv, self).__init__()
        self.num_nodes = num_nodes
        self.max_channel_offsets = max_channel_offsets
        self.max_slotframe_size = max_slotframe_size
        # We define the number of actions
        # 1) change parent node of a specific node (size: 1 * num_nodes * num_nodes)
        # 2) increase the length of the slotframe
        # 3) decrease the length of the slotframe
        # -- 4) change timeoffset of a specific node (size: 1 * num_nodes)
        # -- 5) change channeloffset of a specific node (size: 1 * num_nodes)
        # 6) add a new RX link of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size )
        # 7) add a new Tx link to parent of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # 8) remove a Tx link to parent of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # 9) remove a Rx link of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # Total number of actions = num_nodes * num_nodes + 1 + 1 + 4 * num_nodes * num_channel_offsets x slotframe_size
        # Total = 2 + num_nodes (num_nodes + 4 * num_channel_offsets x slotframe_size)
        n_actions = 2 + self.num_nodes * \
            (self.num_nodes + 4 * self.max_channel_offsets * self.max_slotframe_size)
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the current user requirements, routing paths, slotframe length, tsch schedules, RSSI and ETX network links.
        # 1) The user requirements is a vector of 1x3 Alpha, Beta, Gamma (ranges from 0 to 1)
        # 2) The routing path is a vector of the routes_matrix of shape num_nodes x num_nodes (1 represents a path between the two nodes)
        # 3) The slotframe length is a number (we can normalize it using the maximum length)
        # 4) The tsch schedules is a vector containing the schedules matrix for each node of size num_channel_offsets x slotframe_size
        # 5) The network RSSI links is a vector containing the current comm. link (size is num_nodes x num_nodes)
        # 6) The network ETX links is a vector containing the current link quality info (size is num_nodes x num_nodes)
        # Total number of observations = 3 + num_nodes x num_nodes + 1 + num_channel_offsets x slotframe_size x num_nodes + num_nodes x num_nodes + num_nodes x num_nodes
        # Total = 4 + num_nodes (num_nodes + num_channel_offsets x slotframe_size + num_nodes + num_nodes)
        # Total = 4 + num_nodes (3 * num_nodes + num_channel_offsets x slotframe_size)
        self.n_observations = 4 + \
            num_nodes * (3 * num_nodes + self.max_channel_offsets *
                         self.max_slotframe_size)
        self.observation_space = spaces.Box(low=0, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    def step(self, action):
        print("Performing action "+str(action))
        observation = np.empty(shape=(self.n_observations,)).astype(np.float32)
        reward = 1
        done = False
        info = {}
        return observation, reward, done, info

    def reset(self):
        """
        Important: the observation must be a numpy array
        :return: (np.array)
        """
        observation = np.empty(shape=(self.n_observations,)).astype(np.float32)
        return observation  # reward, done, info can't be included

    def render(self, mode='human'):
        print("rendering")

    def close(self):
        pass
