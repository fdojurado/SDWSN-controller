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

import numpy as np

import logging


logger = logging.getLogger(f'main.{__name__}')


class NumericalRewardProcessing(RewardProcessing):
    def __init__(
        self,
        config,
        **kwargs
    ):
        # Power polynomials coefficients
        self.power_trendpoly = np.poly1d(
            config.performance_metrics.energy.weights)
        # delay polynomials coefficients
        self.delay_trendpoly = np.poly1d(
            config.performance_metrics.delay.weights)
        # PDR polynomials coefficients
        self.pdr_trendpoly = np.poly1d(config.performance_metrics.pdr.weights)
        # offsets
        self.__power_norm_offset = config.performance_metrics.energy.norm_offset
        self.__delay_norm_offset = config.performance_metrics.delay.norm_offset
        self.__reliability_norm_offset = config.performance_metrics.pdr.norm_offset
        # Reward processor name
        self.__name = "Numerical Reward Processor"
        self.__network = kwargs.get("network")

        super().__init__()

    @property
    def name(self):
        return self.__name

    def calculate_reward(self, alpha, beta, delta, sf_size):
        """
        Function to calculate the reward given the SF size
        """
        # Calculate power consumption
        power_normalized = self.power_trendpoly(
            sf_size)+self.__power_norm_offset
        # Calculate delay consumption
        delay_normalized = self.delay_trendpoly(
            sf_size)+self.__delay_norm_offset
        # Calculate pdr consumption
        pdr_normalized = self.pdr_trendpoly(
            sf_size)+self.__reliability_norm_offset
        # Calculate the reward
        reward = 2-1*(alpha*power_normalized+beta *
                      delay_normalized-delta*pdr_normalized)
        # print(f"reward: {reward}")
        info = {
            "reward": reward,
            "power_normalized": power_normalized,
            "delay_normalized": delay_normalized,
            "pdr_mean": pdr_normalized
        }
        return info
