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

from sdwsn_controller.controller.rl_base_controller import RLBaseController
from sdwsn_controller.controller.base_controller import BaseController
from sdwsn_controller.docker.docker import CoojaDocker

from typing import Dict
from time import sleep
import logging

logger = logging.getLogger('main.'+__name__)


class ContainerController(BaseController, RLBaseController):
    def __init__(
        self,
        # Container related
        image: str = 'contiker/contiki-ng',
        container_port: int = 60001,
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
        container_ports = {
            'container': container_port,
            'host': container_port
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
        logger.info(f'Container port: {container_port}')

        # Container
        self.container = CoojaDocker(image=image, command=command, mount=mount,
                                     sysctls=sysctls, ports=container_ports, privileged=privileged, detach=detach,
                                     socket_file=socket_file)

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
