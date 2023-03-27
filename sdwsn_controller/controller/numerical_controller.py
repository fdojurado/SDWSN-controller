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
from datetime import datetime

from sdwsn_controller.controller.base_controller import BaseController

import logging

logger = logging.getLogger(f'main.{__name__}')


class NumericalController(BaseController):
    def __init__(
        self,
        config
    ):

        logger.info("Building numerical controller")

        super().__init__(
            config=config
        )

    # Controller related functions
    def timeout(self):
        pass

    def wait(self):
        return 1

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

    def reset(self):
        self.start()

    def processing_wait(self, _):
        pass

    def get_state(self):
        # Let's return the user requirements, last tsch schedule, current slotframe size
        state = {
            "user_requirements": self.user_requirements,
            "alpha": self.alpha,
            "beta": self.beta,
            "delta": self.delta,
            "last_ts_in_schedule": self.last_tsch_link,
            "current_sf_len": self.current_slotframe_size
        }
        return state

    def calculate_reward(self, alpha, beta, delta, slotframe_size):
        sample_time = datetime.now().timestamp() * 1000.0
        reward = self.reinforcement_learning.calculate_reward(
            alpha, beta, delta, slotframe_size)
        info = {
            "timestamp": sample_time,
            "alpha": alpha,
            "beta": beta,
            "delta": delta,
            'power_wam': reward['power_normalized'],
            'power_mean': reward['power_normalized'],
            'power_normalized': reward['power_normalized'],
            'delay_wam': reward['delay_normalized'],
            'delay_mean': reward['delay_normalized'],
            'delay_normalized': reward['delay_normalized'],
            'pdr_wam': reward['pdr_mean'],
            'pdr_mean': reward['pdr_mean'],
            'current_sf_len': self.current_slotframe_size,
            'last_ts_in_schedule': self.last_tsch_link,
            'reward': reward['reward']
        }
        return info
