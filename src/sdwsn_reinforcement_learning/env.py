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

from sdwsn_tsch.schedule import Schedule
from sdwsn_routes.routes import Routes

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27


class Env(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, max_channel_offsets=3, max_slotframe_size=100):
        super(Env, self).__init__()
        self.max_channel_offsets = max_channel_offsets
        self.max_slotframe_size = max_slotframe_size
        # Set sequence to 0
        self.sequence = 0
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
