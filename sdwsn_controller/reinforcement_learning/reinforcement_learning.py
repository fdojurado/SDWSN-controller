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
from sdwsn_controller.reinforcement_learning.reward_processing import RewardProcessing

import logging

logger = logging.getLogger(f'main.{__name__}')


class ReinforcementLearning():

    def __init__(
            self,
            env,
            reward_processor
    ) -> None:

        self.env = env
        self.reward_processor = reward_processor
        self.callback = None

        logger.info(f"RL reward processor: {self.reward_processor.name}")

    @property
    def env(self):
        return self.__env

    @env.setter
    def env(self, val):
        self.__env = val

    @ property
    def reward_processor(self):
        return self.__reward_processor

    @ reward_processor.setter
    def reward_processor(self, val):
        assert isinstance(val, RewardProcessing)
        self.__reward_processor = val

    def register_callback(self, callback):
        self.callback = callback

    def calculate_reward(self, alpha, beta, delta, sf):
        reward = self.reward_processor.calculate_reward(alpha, beta, delta, sf)
        if self.callback:
            self.callback(reward)
        return reward
