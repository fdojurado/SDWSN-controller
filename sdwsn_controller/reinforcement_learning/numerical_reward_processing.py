import numpy as np
from sdwsn_controller.database.db_manager import DatabaseManager, SLOT_DURATION
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.reinforcement_learning.reward_processing import RewardProcessing


class NumericalRewardProcessing(RewardProcessing):
    def __init__(
        self,
        power_weights: np.array() = np.array(
            [-2.34925404e-06,  2.38160571e-04, -8.87979911e-03, 3.25046326e-01]
        ),
        delay_weights: np.array() = np.array(
            [-3.52867079e-06, 2.68498049e-04, -2.37508338e-03, 4.84268817e-02]
        ),
        pdr_weights: np.array() = np.array(
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
        power = self.power_trendpoly(sf_size)
        # Calculate delay consumption
        delay = self.delay_trendpoly(sf_size)
        # Calculate pdr consumption
        pdr = self.pdr_trendpoly(sf_size)
        # Calculate the reward
        reward = -1*(alpha*power+beta * delay-delta*pdr)
        # print(f"reward: {reward}")
        return reward, power, delay, pdr
