import imp
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
                [3.72158335e-08, -5.52679120e-06,
                    3.06757888e-04, -7.85850498e-03, 9.50518299e-01]
            ),
            delay_weights=np.array(
                [3.17334712e-07, -2.40848429e-05,  1.27791635e-03, -4.89649727e-03]
            ),
            pdr_weights=np.array(
                [-5.85240204e-04,  9.65952384e-01]
            )
        )

        super().__init__(
            self.simulation_name,
            controller)
