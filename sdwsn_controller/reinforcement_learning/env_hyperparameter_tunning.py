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

from sdwsn_controller.reinforcement_learning.env import Env
from random import randint
from sdwsn_controller.controller.env_numerical_controller import EnvNumericalController
import numpy as np


class HyperparameterEnv(Env):

    def __init__(self):

        self.simulation_name = 'hyperparameter_tunning_'+str(randint(0, 1e5))

        # Controller instance
        controller = EnvNumericalController(
            power_weights=np.array(
                [1.14247726e-08, -2.22419840e-06,
                 1.60468046e-04, -5.27254015e-03, 9.35384746e-01]
            ),
            delay_weights=np.array(
                # [-2.98849631e-08,  4.52324093e-06,  5.80710379e-04,  1.02710258e-04]
                [-2.98849631e-08,  4.52324093e-06,  5.80710379e-04,
                 0.85749587960003453947587046868728]
            ),
            pdr_weights=np.array(
                # [-2.76382789e-04,  9.64746733e-01]
                [-2.76382789e-04,  -0.8609615946299346738365592202098]
            )
        )

        super().__init__(
            self.simulation_name,
            controller)
