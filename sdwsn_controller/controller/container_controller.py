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

from sdwsn_controller.controller.base_controller import BaseController
from sdwsn_controller.docker.docker import CoojaDocker

from typing import Dict
from time import sleep
import logging

logger = logging.getLogger('main.'+__name__)


class ContainerController(BaseController):
    def __init__(
        self,
        # Container related
        docker_image: str = 'contiker/contiki-ng',
        port: int = 60001,
        script: str = '/bin/sh -c "cd examples/elise && ./run-cooja.py"',
        docker_target: str = '/home/user/contiki-ng',
        contiki_source: str = '/Users/fernando/contiki-ng',
        sysctls: Dict = {
            'net.ipv6.conf.all.disable_ipv6': 0
        },
        privileged: bool = True,
        detach: bool = True,
        log_file: str = '/Users/fernando/contiki-ng/examples/elise/COOJA.log',
        # Sink/socket communication
        socket: object = None,
        # Database
        db: object = None,
        # RL related
        reward_processing: object = None,
        # Packet dissector
        packet_dissector: object = None,
        # Window
        processing_window: int = 200,
        # Routing
        router: object = None,
        # TSCH scheduler
        tsch_scheduler: object = None
    ):
        """
        This controller is intended to run with Cooja hosted in Docker (without GUI).

        Args:
            docker_image (str, optional): Docker image name. Defaults to 'contiker/contiki-ng'.
            port (int, optional): Port of the sink. Defaults to 60001.
            script (str, optional): Command to run the simulation script. Defaults to \
                '/bin/sh -c "cd examples/elise && ./run-cooja.py"'.
            docker_target (str, optional): Contiki-NG folder path in Docker. Defaults to '/home/user/contiki-ng'.
            contiki_source (str, optional): Contiki-NG source folder. Defaults to '/Users/fernando/contiki-ng'.
            sysctls (_type_, optional): Kernel parameters to set in the container. Defaults to \
                { 'net.ipv6.conf.all.disable_ipv6': 0 }.
            privileged (bool, optional): Give extended privileges to this container. Defaults to True.
            detach (bool, optional): Run container in the background. Defaults to True.
            log_file (str, optional): Path to the 'COOJA.log' file. Defaults to \
                '/Users/fernando/contiki-ng/examples/elise/COOJA.log'.
            socket (SerialBus object, optional): Serial connection to the sink. Defaults to None.
            db (Database object, optional): Database. Defaults to None.
            reward_processing (RewardProcessing object, optional):Reward processing for RL. Defaults to None.
            packet_dissector (Dissector object, optional): Packet dissector. Defaults to None.
            processing_window (int, optional): Number of packets for a new cycle. Defaults to 200.
            router (Router object, optional): Centralized routing algorithm. Defaults to None.
            tsch_scheduler (Scheduler object, optional): Centralized TSCH scheduler. Defaults to None.
        """
        ports = {
            'container': port,
            'host': port
        }

        mount = {
            'target': docker_target,
            'source': contiki_source,
            'type': 'bind'
        }

        logger.info("Building a containerized controller")
        logger.info(f"docker_image: {docker_image}")
        logger.info(f"script: {script}")
        logger.info(f'docker_target: {docker_target}')
        logger.info(f'contiki_source: {contiki_source}')
        logger.info(f'socket file: {log_file}')
        logger.info(f'Container port: {port}')

        # Container
        self.container = CoojaDocker(docker_image=docker_image, script=script, mount=mount,
                                     sysctls=sysctls, ports=ports, privileged=privileged, detach=detach,
                                     log_file=log_file)

        super().__init__(
            socket=socket,
            db=db,
            reward_processing=reward_processing,
            packet_dissector=packet_dissector,
            processing_window=processing_window,
            router=router,
            tsch_scheduler=tsch_scheduler
        )

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
