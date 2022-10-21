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
from sdwsn_controller.database.db_manager import DatabaseManager


class ReinforcementLearningController(BaseController):
    """

    A reinforcement learning controller.

    Args:
        BaseController (_type_): _description_
    """

    def __init__(
        self,
        db_name: str = None,
        db_host: str = None,
        db_port: int = None
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

        super().__init__()

    @property
    def db(self):
        return self.__db

    def save_observations(self, **env_kwargs):
        if self.__db is not None:
            self.__db.save_observations(**env_kwargs)

        self.update_observations(**env_kwargs)

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
