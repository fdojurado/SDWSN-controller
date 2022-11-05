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
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.reinforcement_learning.reward_processing import EmulatedRewardProcessing
from sdwsn_controller.serial.serial import SerialBus
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.database.db_manager import SLOT_DURATION
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.docker.docker import CoojaDocker
from sdwsn_controller.routing.dijkstra import Dijkstra

from rich.progress import Progress
from typing import Dict
from time import sleep
import logging

logger = logging.getLogger('main.'+__name__)


class RLContainerController(ReinforcementLearningController):
    def __init__(
        self,
        # Container related
        image: str = 'contiker/contiki-ng',
        command: str = '/bin/sh -c "cd examples/benchmarks/rl-sdwsn && ./run-cooja.py"',
        target: str = '/home/user/contiki-ng',
        source: str = '/Users/fernando/contiki-ng',
        sysctls: Dict = {
            'net.ipv6.conf.all.disable_ipv6': 0
        },
        privileged: bool = True,
        detach: bool = True,
        socket_file: str = '/Users/fernando/contiki-ng/examples/benchmarks/rl-sdwsn/COOJA.log',
        # Sink/socket communication
        socket_address: str = '127.0.0.1',
        socket_port: int = 60001,
        # Database
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        # Simulation
        simulation_name: str = 'mySimulation',
        # RL related
        power_min: int = 0,
        power_max: int = 5000,
        delay_min: int = SLOT_DURATION,
        delay_max: int = 15000,
        power_norm_offset: float = 0.0,
        delay_norm_offset: float = 0.0,
        reliability_norm_offset: float = 0.0,
        processing_window: int = 200,
        # Routing
        router: object = Dijkstra(),
        # TSCH scheduler
        tsch_scheduler: object = ContentionFreeScheduler(500, 3)
    ):
        container_ports = {
            'container': socket_port,
            'host': socket_port
        }

        mount = {
            'target': target,
            'source': source,
            'type': 'bind'
        }

        logger.info("Building a containerized controller")
        logger.info(f"Image: {image}")
        logger.info(f"command: {command}")
        logger.info(f'target: {target}')
        logger.info(f'source: {source}')
        logger.info(f'socket file: {socket_file}')
        logger.info(f'cooja port: {socket_port}')
        logger.info(f'DB name: {db_name}')
        logger.info(f'simulation name: {simulation_name}')

        # Container
        self.container = CoojaDocker(image=image, command=command, mount=mount,
                                     sysctls=sysctls, ports=container_ports, privileged=privileged, detach=detach,
                                     socket_file=socket_file)

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

    # Controller related functions

    def timeout(self):
        sleep(1.2)

    def start(self):
        self.container.start_container()
        super().start()

    def stop(self):
        self.container.shutdown()
        super().stop()

    def reset(self):
        logger.info('Resetting container, controller, etc.')
        self.stop()
        self.start()
