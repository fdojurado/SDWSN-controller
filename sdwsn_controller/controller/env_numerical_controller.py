from sdwsn_controller.controller.controller import BaseController
from sdwsn_controller.reinforcement_learning.numerical_reward_processing import NumericalRewardProcessing
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.database.database import OBSERVATIONS
from random import randrange
import random


import numpy as np


class EnvNumericalController(BaseController):
    def __init__(
        self,
        alpha: float = None,
        beta: float = None,
        delta: float = None,
        db_name: str = None,
        db_host: str = None,
        db_port: int = None,
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
        if db_name is not None and db_host is not None and db_port is not None:
            # Create database
            self.__db = DatabaseManager(
                name=db_name,
                host=db_host,
                port=db_port
            )
        else:
            self.__db = None

        # Create reward module
        self.__reward_processing = NumericalRewardProcessing(
            power_weights=power_weights,
            delay_weights=delay_weights,
            pdr_weights=pdr_weights
        )

        # Initialize observation variables
        self.timestamp = 0
        self._alpha = alpha
        self._beta = beta
        self._delta = delta
        self.power_wam = 0
        self.power_mean = 0
        self.power_normalized = 0
        self.delay_wam = 0
        self.delay_mean = 0
        self.delay_normalized = 0
        self.pdr_wam = 0
        self.pdr_mean = 0
        self.current_sf_len = 0
        self.last_ts_in_schedule = 0
        self.reward = 0

        super().__init__()

    """ 
        Class related functions 
    """

    def update_observations(self, timestamp, alpha, beta, delta, power_wam, power_mean,
                            power_normalized, delay_wam, delay_mean, delay_normalized,
                            pdr_wam, pdr_mean, current_sf_len, last_ts_in_schedule, reward):
        self.timestamp = timestamp
        self.user_requirements(alpha, beta, delta)
        self.power_wam = power_wam
        self.power_mean = power_mean
        self.power_normalized = power_normalized
        self.delay_wam = delay_wam
        self.delay_mean = delay_mean
        self.delay_normalized = delay_normalized
        self.pdr_wam = pdr_wam
        self.pdr_mean = pdr_mean
        self.current_sf_len = current_sf_len
        self.last_ts_in_schedule = last_ts_in_schedule
        self.reward = reward

    """ 
        Controller related functions
    """

    def increase_sequence(self):
        pass

    def increase_cycle_sequence(self):
        pass

    def reset_pkt_sequence(self):
        pass

    def get_cycle_sequence(self):
        pass

    @property
    def db(self):
        return self.__db

    def export_db(self, simulation_name, folder):
        if self.db is not None:
            self.db.export_collection(OBSERVATIONS, simulation_name, folder)

    @property
    def packet_dissector(self):
        return

    @property
    def sequence(self):
        return

    @sequence.setter
    def sequence(self):
        pass

    @property
    def cycle_sequence(self):
        return

    @cycle_sequence.setter
    def cycle_sequence(self):
        pass

    def init_db(self):
        if self.__db is not None:
            self.__db.initialize()

    def start(self):
        # Initialize database
        self.init_db()
        return super().start()

    def stop(self):
        pass

    def reset(self):
        self.start()

    def wait(self):
        return 1

    def wait_seconds(self, seconds):
        pass

    def send(self):
        pass

    def reliable_send(self):
        pass

    def save_observations(self, **env_kwargs):
        if self.__db is not None:
            self.__db.save_observations(**env_kwargs)
        else:
            self.update_observations(**env_kwargs)

    def get_state(self):
        # Let's return the user requirements, last tsch schedule, current slotframe size
        alpha, beta, delta = self.user_requirements
        return alpha, beta, delta, self.last_ts_in_schedule, self.current_sf_len

    # def get_last_observations(self):
    #     if self.__db is not None:
    #         return self.__db.get_last_observations()
    #     else:
    #         return self._alpha, self._beta, self._delta, self.last_ts_in_schedule, self.current_sf_len, None, None

    def delete_info_collection(self):
        if self.__db is not None:
            self.__db.delete_collection(NODES_INFO)

    def calculate_reward(self, alpha, beta, delta, slotframe_size):
        return self.__reward_processing.calculate_reward(alpha, beta, delta, slotframe_size)

    @property
    def user_requirements(self):
        if self._alpha is None or self._beta is None or self._delta is None:
            # If this is not set, we then generate them randomly
            balanced = [0.4, 0.3, 0.3]
            energy = [0.8, 0.1, 0.1]
            delay = [0.1, 0.8, 0.1]
            reliability = [0.1, 0.1, 0.8]
            user_req = [balanced, energy, delay, reliability]
            select_user_req = random.choice(user_req)
            return select_user_req[0], select_user_req[1], select_user_req[2]
        else:
            return self._alpha, self._beta, self._delta

    @user_requirements.setter
    def user_requirements(self, alpha, beta, delta):
        self._alpha = alpha
        self._beta = beta
        self._delta = delta

    def get_network_links(self):
        pass

    def comm_interface_start(self):
        pass

    def comm_interface_stop(self):
        pass

    def comm_interface_read(self):
        pass

    def send_tsch_schedules(self, slotframe_size):
        pass

    def last_active_tsch_slot(self):
        return randrange(9+1, 20)

    def compute_tsch_schedule(self, path, slotframe_size):
        pass

    def send_routes(self):
        pass

    def compute_dijkstra(self, G):
        pass
