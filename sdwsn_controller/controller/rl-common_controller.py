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

from matplotlib import use
from sdwsn_controller.controller.reinforcement_learning_controller import ReinforcementLearningController
from sdwsn_controller.common import common
from sdwsn_controller.packet.packet import RA_Packet_Payload
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.serial.serial import SerialBus
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.reinforcement_learning.reward_processing import EmulatedRewardProcessing
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.packet.packet import Cell_Packet_Payload
from sdwsn_controller.database.db_manager import SLOT_DURATION
from sdwsn_controller.database.database import OBSERVATIONS

from typing import Dict
import numpy as np
import networkx as nx
import threading
from time import sleep
import logging

logger = logging.getLogger('main.'+__name__)


class RLCommonController(ReinforcementLearningController):

    def __init__(
        self,
        socket_address: str = '127.0.0.1',
        socket_port: int = 60001,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        router: object = Dijkstra(),
        tsch_scheduler: object = ContentionFreeScheduler(500, 3),
        power_min: int = 0,
        power_max: int = 5000,
        delay_min: int = SLOT_DURATION,
        delay_max: int = 15000,
        power_norm_offset: float = 0.0,
        delay_norm_offset: float = 0.0,
        reliability_norm_offset: float = 0.0,
        processing_window: int = 60
    ):
        # Create database manager
        self.__db = DatabaseManager(
            name=db_name,
            host=db_host,
            port=db_port
        )

        # Create packet dissector
        self.__packet_dissector = PacketDissector(database=self.db)

        # Create TSCH scheduler module
        self.__tsch_scheduler = tsch_scheduler

        # Create an instance of Router
        self.__router = router

        # Create a socket/sink communication
        self.__socket = SerialBus(socket_address, socket_port)

        # Processing window
        self.__processing_window = processing_window

        # Create reward module
        self.__reward_processing = EmulatedRewardProcessing(
            database=self.db,
            power_min=power_min,
            power_max=power_max,
            delay_min=delay_min,
            delay_max=delay_max,
            power_norm_offset=power_norm_offset,
            delay_norm_offset=delay_norm_offset,
            reliability_norm_offset=reliability_norm_offset
        )

        super().__init__()

    # Database
    @property
    def db(self):
        return self.__db

    # Packet dissector
    @property
    def packet_dissector(self):
        return self.__packet_dissector

    # TSCH scheduler
    @property
    def tsch_scheduler(self):
        return self.__tsch_scheduler

    # Routing
    def router(self):
        return self.__router

    # Serial Interface
    @property
    def socket(self):
        return self.__socket

    # Processing window
    @property
    def processing_window(self):
        return self.__processing_window

    @processing_window.setter
    def processing_window(self, val):
        self.__processing_window = val

    # Reinforcement learning functionalities
    def calculate_reward(self, alpha, beta, delta, slotframe_size):
        return self.__reward_processing.calculate_reward(alpha, beta, delta, self.cycle_sequence)
