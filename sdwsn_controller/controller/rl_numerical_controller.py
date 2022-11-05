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

from sdwsn_controller.controller.reinforcement_learning_controller import ReinforcementLearningController
from sdwsn_controller.reinforcement_learning.numerical_reward_processing import NumericalRewardProcessing
from sdwsn_controller.database.db_manager import DatabaseManager
from typing import Dict


import numpy as np


class NumericalRewardProcessing():
    def __init__(
        self,
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
        # Power polynomials coefficients
        self.power_trendpoly = np.poly1d(power_weights)
        # delay polynomials coefficients
        self.delay_trendpoly = np.poly1d(delay_weights)
        # PDR polynomials coefficients
        self.pdr_trendpoly = np.poly1d(pdr_weights)
        super().__init__()

    def calculate_reward(self, alpha, beta, delta, sf_size):
        """
        Function to calculate the reward given the SF size 
        """
        # Calculate power consumption
        power_normalized = self.power_trendpoly(sf_size)
        power = [0, 0, power_normalized]
        # Calculate delay consumption
        delay_normalized = self.delay_trendpoly(sf_size)
        delay = [0, 0, delay_normalized]
        # Calculate pdr consumption
        pdr_normalized = self.pdr_trendpoly(sf_size)
        pdr = [0, pdr_normalized]
        # Calculate the reward
        reward = 2-1*(alpha*power_normalized+beta *
                      delay_normalized-delta*pdr_normalized)
        # print(f"reward: {reward}")
        return reward, power, delay, pdr


class RLNumericalController(ReinforcementLearningController):
    def __init__(
        self,
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
        # We only create a DB if this is explicitly pass to the class.
        # This is done to speed up the training in the numerical env.
        if db_name is not None and db_host is not None and db_port is not None:
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

        super().__init__()

    # Database
    @property
    def db(self):
        return self.__db

    # Packet dissector
    @property
    def packet_dissector(self):
        return None

    # Override some TSCH functions
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

    @property
    def tsch_scheduler(self):
        return None

    # Routing
    @property
    def router(self):
        return None

    # Serial Interface
    @property
    def socket(self):
        return None

    # No processing window
    @property
    def processing_window(self):
        return None

    @processing_window.setter
    def processing_window(self, val):
        pass

    def timeout(self):
        pass

    def reset(self):
        self.start()

    def processing_wait(self, _):
        pass

    def calculate_reward(self, alpha, beta, delta, slotframe_size):
        return self.__reward_processing.calculate_reward(alpha, beta, delta, slotframe_size)
