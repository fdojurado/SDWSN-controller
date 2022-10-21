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

from sdwsn_controller.controller.controller import BaseController
from sdwsn_controller.reinforcement_learning.numerical_reward_processing import NumericalRewardProcessing
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.database.database import OBSERVATIONS
from random import randrange
import random


import numpy as np


class EnvNumericalController(BaseController):
    def __init__(
        self,
        alpha: float = None,
        beta: float = None,
        delta: float = None,
        db_name: str = None,
        db_host: str = None,
        db_port: int = None,
        power_weights: np = np.array(
            [-2.34925404e-06,  2.38160571e-04, -8.87979911e-03, 3.25046326e-01]
        ),
        delay_weights: np = np.array(
            [-3.52867079e-06, 2.68498049e-04, -2.37508338e-03, 4.84268817e-02]
        ),
        pdr_weights: np = np.array(
            [-0.00121819, 0.88141225]
        )
    ):
        if db_name is not None and db_host is not None and db_port is not None:
            # Create database
            self.__db = DatabaseManager(
                name=db_name,
                host=db_host,
                port=db_port
            )
        else:
            self.__db = None

        # Create reward module
        self.__reward_processing = NumericalRewardProcessing(
            power_weights=power_weights,
            delay_weights=delay_weights,
            pdr_weights=pdr_weights
        )

        # Initialize observation variables
        self.timestamp = 0
        self.__alpha = alpha
        self.__beta = beta
        self.__delta = delta
        self.power_wam = 0
        self.power_mean = 0
        self.power_normalized = 0
        self.delay_wam = 0
        self.delay_mean = 0
        self.delay_normalized = 0
        self.pdr_wam = 0
        self.pdr_mean = 0
        self.__current_slotframe_size = 0
        self.__last_tsch_link = 0
        self.reward = 0

        super().__init__()

    """ 
        Class related functions 
    """

    def update_observations(self, timestamp, alpha, beta, delta, power_wam, power_mean,
                            power_normalized, delay_wam, delay_mean, delay_normalized,
                            pdr_wam, pdr_mean, current_sf_len, last_ts_in_schedule, reward):
        self.timestamp = timestamp
        self.user_requirements = (alpha, beta, delta)
        self.power_wam = power_wam
        self.power_mean = power_mean
        self.power_normalized = power_normalized
        self.delay_wam = delay_wam
        self.delay_mean = delay_mean
        self.delay_normalized = delay_normalized
        self.pdr_wam = pdr_wam
        self.pdr_mean = pdr_mean
        self.current_slotframe_size = current_sf_len
        self.last_tsch_link = last_ts_in_schedule
        self.reward = reward

    """ 
        Controller related functions
    """

    def increase_sequence(self):
        pass

    def increase_cycle_sequence(self):
        pass

    def reset_pkt_sequence(self):
        pass

    def get_cycle_sequence(self):
        pass

    @property
    def db(self):
        return self.__db

    def export_db(self, simulation_name, folder):
        if self.db is not None:
            self.db.export_collection(OBSERVATIONS, simulation_name, folder)

    @property
    def packet_dissector(self):
        return

    @property
    def sequence(self):
        return

    @sequence.setter
    def sequence(self):
        pass

    @property
    def cycle_sequence(self):
        return

    @cycle_sequence.setter
    def cycle_sequence(self):
        pass

    def init_db(self):
        if self.__db is not None:
            self.__db.initialize()

    def start(self):
        # Initialize database
        self.init_db()
        return super().start()

    def stop(self):
        pass

    def reset(self):
        self.start()

    def wait(self):
        return 1

    def wait_seconds(self, seconds):
        pass

    def send(self):
        pass

    def reliable_send(self):
        pass

    def save_observations(self, **env_kwargs):
        if self.__db is not None:
            self.__db.save_observations(**env_kwargs)

        self.update_observations(**env_kwargs)

    def get_state(self):
        # Let's return the user requirements, last tsch schedule, current slotframe size
        alpha, beta, delta = self.user_requirements
        return alpha, beta, delta, self.last_tsch_link, self.current_slotframe_size

    def delete_info_collection(self):
        if self.__db is not None:
            self.__db.delete_collection(NODES_INFO)

    def calculate_reward(self, alpha, beta, delta, slotframe_size):
        return self.__reward_processing.calculate_reward(alpha, beta, delta, slotframe_size)

    @property
    def user_requirements(self):
        return self.__alpha, self.__beta, self.__delta

    @user_requirements.setter
    def user_requirements(self, val):
        try:
            alpha, beta, delta = val
        except ValueError:
            raise ValueError("Pass an iterable with three items")
        else:
            """ This will run only if no exception was raised """
            self.__alpha = alpha
            self.__beta = beta
            self.__delta = delta

    @property
    def last_tsch_link(self):
        return self.__last_tsch_link

    @last_tsch_link.setter
    def last_tsch_link(self, val):
        self.__last_tsch_link = val

    @property
    def current_slotframe_size(self):
        return self.__current_slotframe_size

    @current_slotframe_size.setter
    def current_slotframe_size(self, val):
        self.__current_slotframe_size = val

    def get_network_links(self):
        pass

    def comm_interface_start(self):
        pass

    def comm_interface_stop(self):
        pass

    def comm_interface_read(self):
        pass

    def send_tsch_schedules(self):
        pass

    def compute_tsch_schedule(self, path, slotframe_size):
        pass

    def send_routes(self):
        pass

    def compute_routes(self, G):
        pass
