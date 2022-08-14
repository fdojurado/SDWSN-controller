""" This is the implementation of the Software-Defined Wireless Sensor Network
environment """
from typing import Type
import gym
from gym import spaces
import numpy as np
from datetime import datetime
import random

from sdwsn_controller.common import common
from sdwsn_controller.result_analysis.run_analysis import run_analysis
from sdwsn_controller.database.db_manager import DatabaseManager
from random import randrange

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27


class Env(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(
            self,
            db_name: str = 'mySDN',
            db_host: str = '127.0.0.1',
            db_port: int = 27017,
            simulation_name: str = 'myNumericalSimulation',
            fig_dir: str = './figures/'
    ):
        super(Env, self).__init__()
        self.fig_dir = fig_dir
        self.simulation_name = simulation_name
        # Save instance of packet dissector
        # Create database
        self.__db = DatabaseManager(
            name=db_name,
            host=db_host,
            port=db_port
        )
        # We define the number of actions
        n_actions = 3  # increase and decrease slotframe size
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the user requirements, power, delay, pdr, last ts active in schedule
        self.n_observations = 7
        self.observation_space = spaces.Box(low=0, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    """ Step action """

    def step(self, action):
        sample_time = datetime.now().timestamp() * 1000.0
        # We now get the last observations
        alpha, beta, delta, last_ts_in_schedule, current_sf_len, _, _ = self.__db.get_last_observations()
        # print("Performing action "+str(action))
        if action == 0:
            # print("increasing slotframe size")
            sf_len = common.next_coprime(current_sf_len)
        if action == 1:
            sf_len = common.previous_coprime(current_sf_len)
            # print("decreasing slotframe size")
        if action == 2:
            sf_len = current_sf_len
        user_requirements = np.array([alpha, beta, delta])
        # Calculate the reward
        reward, cycle_power, cycle_delay, cycle_pdr = self.__calculate_reward(
            alpha, beta, delta, sf_len)
        # Append to the observations
        sample_time = datetime.now().timestamp() * 1000.0
        observation = np.append(user_requirements, cycle_power)
        observation = np.append(observation, cycle_delay)
        observation = np.append(observation, cycle_pdr)
        observation = np.append(observation, last_ts_in_schedule/15)
        self.__db.save_observations(
            timestamp=sample_time,
            alpha=alpha,
            beta=beta,
            delta=delta,
            power_mean=cycle_power,
            delay_mean=cycle_delay,
            pdr_mean=cycle_pdr,
            current_sf_len=sf_len,
            last_ts_in_schedule=last_ts_in_schedule,
            reward=reward
        )
        done = False
        info = {}
        # 50 is the maximum slotframe size
        # TODO: Set the maximum slotframe size at the creation
        # of the environment
        if (sf_len < last_ts_in_schedule or sf_len > 50):
            done = True
            reward = -4
        return observation, reward, done, info

    def __calculate_reward(self, alpha, beta, delta, sf_size):
        """
        Function to calculate the reward given the SF size 
        """
        # Power polynomials coefficients
        power_trend = np.array(
            [-2.34925404e-06,  2.38160571e-04, -8.87979911e-03, 3.25046326e-01])
        power_trendpoly = np.poly1d(power_trend)
        # delay polynomials coefficients
        delay_trend = np.array(
            [-3.52867079e-06, 2.68498049e-04, -2.37508338e-03, 4.84268817e-02])
        delay_trendpoly = np.poly1d(delay_trend)
        # PDR polynomials coefficients
        pdr_trend = np.array(
            [-0.00121819, 0.88141225])
        pdr_trendpoly = np.poly1d(pdr_trend)
        # Calculate power consumption
        power = power_trendpoly(sf_size)
        # Calculate delay consumption
        delay = delay_trendpoly(sf_size)
        # Calculate pdr consumption
        pdr = pdr_trendpoly(sf_size)
        # Calculate the reward
        reward = -1*(alpha*power+beta * delay-delta*pdr)
        # print(f"reward: {reward}")
        return reward, power, delay, pdr

    """ Reset the environment, reset the routing and the TSCH schedules """

    def reset(self):
        # Initialize database
        self.__db.initialize()
        # Set the last active timeslot
        last_ts_in_schedule = randrange(10, 15)
        # Set the slotframe size
        slotframe_size = randrange(last_ts_in_schedule+1, 45)
        # We now set and save the user requirements
        balanced = [0.4, 0.3, 0.3]
        energy = [0.8, 0.1, 0.1]
        delay = [0.1, 0.8, 0.1]
        reliability = [0.1, 0.1, 0.8]
        user_req = [balanced, energy, delay, reliability]
        select_user_req = random.choice(user_req)
        # We now save the user requirements
        user_requirements = np.array(select_user_req)
        _, cycle_power, cycle_delay, cycle_pdr = self.__calculate_reward(
            select_user_req[0], select_user_req[1], select_user_req[2], slotframe_size)
        # Append to the observations
        sample_time = datetime.now().timestamp() * 1000.0
        observation = np.append(user_requirements, cycle_power)
        observation = np.append(observation, cycle_delay)
        observation = np.append(observation, cycle_pdr)
        observation = np.append(observation, last_ts_in_schedule/15)
        self.__db.save_observations(
            timestamp=sample_time,
            alpha=select_user_req[0],
            beta=select_user_req[1],
            delta=select_user_req[2],
            power_mean=cycle_power,
            delay_mean=cycle_delay,
            pdr_mean=cycle_pdr,
            current_sf_len=slotframe_size,
            last_ts_in_schedule=last_ts_in_schedule,
            reward=None
        )
        return observation  # reward, done, info can't be included

    def render(self, mode='console'):
        print(f"mode: {mode}")
        # if mode != 'console':
        #     raise NotImplementedError()
        # agent is represented as a cross, rest as a dot
        print('rendering')
        number = random.randint(0, 100)
        run_analysis(self.packet_dissector,
                     self.simulation_name+str(number), self.fig_dir, False)
