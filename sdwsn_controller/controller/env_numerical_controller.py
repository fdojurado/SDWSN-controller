from sdwsn_controller.controller.controller import BaseController
from sdwsn_controller.reinforcement_learning.numerical_reward_processing import NumericalRewardProcessing
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.routes.router import SimpleRouter
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.database.db_manager import SLOT_DURATION
from random import randrange


from typing import Dict
from time import sleep
import numpy as np


class EnvNumericalController(BaseController):
    def __init__(
        self,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
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
        # Create database
        self.__db = DatabaseManager(
            name=db_name,
            host=db_host,
            port=db_port
        )

        # Create reward module
        self.__reward_processing = NumericalRewardProcessing(
            power_weights=power_weights,
            delay_weights=delay_weights,
            pdr_weights=pdr_weights
        )

        super().__init__()

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

    def start(self):
        # Initialize database
        self.init_db()
        return super().start()

    def stop(self):
        pass

    def reset(self):
        print('Resetting numerical controller, etc.')
        self.start()

    def wait(self):
        pass

    def reliable_send(self):
        pass

    def calculate_reward(self, alpha, beta, delta, slotframe_size):
        return self.__reward_processing.calculate_reward(alpha, beta, delta, slotframe_size)

    def get_network_links(self):
        pass

    def comm_interface_start(self):
        pass

    def comm_interface_stop(self):
        pass

    def comm_interface_read(self):
        pass

    def send_tsch_schedules(self):
        pass

    def last_active_tsch_slot(self):
        return randrange(10, 15)

    def compute_tsch_schedule(self):
        pass

    def send_routes(self):
        pass

    def compute_dijkstra(self):
        pass
