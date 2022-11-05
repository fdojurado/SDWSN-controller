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

from sdwsn_controller.database.database import OBSERVATIONS
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.controller.controller import BaseController

import numpy as np
import logging

logger = logging.getLogger('main.'+__name__)


class ReinforcementLearningController(BaseController):
    """

    A reinforcement learning controller that is meant to be flexible;
    therefore, modules such DB, router, TSCH scheduler, serial comm., packet
    dissector are added in the classes that inherits from this class.
    """

    def __init__(
        self,
    ):

        # Initialize observation variables
        self.__timestamp = 0
        self.__power_wam = 0
        self.__power_mean = 0
        self.__power_normalized = 0
        self.__delay_wam = 0
        self.__delay_mean = 0
        self.__delay_normalized = 0
        self.__pdr_wam = 0
        self.__pdr_mean = 0
        self.__current_slotframe_size = 0
        self.__last_tsch_link = 0
        self.__reward = 0

        # Requirements
        self.__user_requirements = UserRequirements()

        super().__init__()

    # -----------------Database functionalities------------------------

    def export_db(self, simulation_name, folder):
        if self.db is not None:
            self.db.export_collection(OBSERVATIONS, simulation_name, folder)
    # ------------------------User requirements------------------------

    @property
    def user_requirements(self):
        return self.__user_requirements.requirements

    @user_requirements.setter
    def user_requirements(self, val):
        self.__user_requirements.requirements = val

    @property
    def alpha(self):
        return self.__user_requirements.alpha

    @alpha.setter
    def alpha(self, val):
        self.__user_requirements.alpha = val

    @property
    def beta(self):
        return self.__user_requirements.beta

    @beta.setter
    def beta(self, val):
        self.__user_requirements.beta = val

    @property
    def delta(self):
        return self.__user_requirements.delta

    @delta.setter
    def delta(self, val):
        self.__user_requirements.delta = val

    # --------------------------Observations----------------------------

    def save_observations(self, **env_kwargs):
        if self.db is not None:
            self.db.save_observations(**env_kwargs)

        self.__update_observations(**env_kwargs)

    def __update_observations(self, timestamp, user_requirements, power_wam, power_mean,
                              power_normalized, delay_wam, delay_mean, delay_normalized,
                              pdr_wam, pdr_mean, current_sf_len, last_ts_in_schedule, reward):
        self.__timestamp = timestamp
        self.user_requirements = user_requirements
        self.__power_wam = power_wam
        self.__power_mean = power_mean
        self.__power_normalized = power_normalized
        self.__delay_wam = delay_wam
        self.__delay_mean = delay_mean
        self.__delay_normalized = delay_normalized
        self.__pdr_wam = pdr_wam
        self.__pdr_mean = pdr_mean
        self.__current_slotframe_size = current_sf_len
        self.__last_tsch_link = last_ts_in_schedule
        self.__reward = reward

    def delete_info_collection(self):
        if self.db is not None:
            self.db.delete_collection(NODES_INFO)

    def get_state(self):
        # Let's return the user requirements, last tsch schedule, current slotframe size
        state = {
            "user_requirements": self.user_requirements,
            "alpha": self.alpha,
            "beta": self.beta,
            "delta": self.delta,
            "last_ts_in_schedule": self.__last_tsch_link,
            "current_sf_len": self.__current_slotframe_size
        }
        return state


class UserRequirements():
    def __init__(self):
        pass

    @property
    def requirements(self):
        user_req = [
            self.alpha,
            self.beta,
            self.delta
        ]
        return np.array(user_req)

    @requirements.setter
    def requirements(self, val):
        try:
            alpha, beta, delta = val
        except ValueError:
            raise ValueError("Pass an iterable with three items")
        else:
            """ This will run only if no exception was raised """
            self.alpha = alpha
            self.beta = beta
            self.delta = delta

    def check_valid_number(func):
        def inner(self, val):
            if val > 1 or val < 0:
                logger.error("Invalid user requirement value.")
                return

            return func(self, val)
        return inner

    @property
    def alpha(self):
        return self.__alpha

    @alpha.setter
    @check_valid_number
    def alpha(self, val):
        self.__alpha = val

    @property
    def beta(self):
        return self.__beta

    @beta.setter
    @check_valid_number
    def beta(self, val):
        self.__beta = val

    @property
    def delta(self):
        return self.__delta

    @delta.setter
    @check_valid_number
    def delta(self, val):
        self.__delta = val
