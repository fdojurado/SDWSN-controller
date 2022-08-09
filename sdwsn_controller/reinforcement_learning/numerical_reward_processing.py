import numpy as np
from sdwsn_controller.database.db_manager import DatabaseManager, SLOT_DURATION
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.reinforcement_learning.reward_processing import RewardProcessing


class NumericalRewardProcessing(RewardProcessing):
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
