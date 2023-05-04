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

import logging

import os

from sdwsn_controller.controller.base_controller import BaseController
from sdwsn_controller.docker.docker import CoojaDocker

from time import sleep
from typing import Dict

logger = logging.getLogger(f'main.{__name__}')


class ContainerController(BaseController):
    def __init__(
        self,
        config,
        sysctls: Dict = {
            'net.ipv6.conf.all.disable_ipv6': 0
        }
    ):
        """
        This controller is intended to run with Cooja hosted in Docker (without GUI).

        Args:
            docker_image (str, optional): Docker image name. Defaults to 'contiker/contiki-ng'.
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
            socket (SinkComm object, optional): Serial connection to the sink. Defaults to None.
            db (Database object, optional): Database. Defaults to None.
            reward_processing (RewardProcessing object, optional):Reward processing for RL. Defaults to None.
            packet_dissector (Dissector object, optional): Packet dissector. Defaults to None.
            processing_window (int, optional): Number of packets for a new cycle. Defaults to 200.
            router (Router object, optional): Centralized routing algorithm. Defaults to None.
            tsch_scheduler (Scheduler object, optional): Centralized TSCH scheduler. Defaults to None.
        """

        ports = {
            'container': config.docker.port,
            'host': config.docker.port
        }

        mount = {
            'target': config.docker.target,
            'source': config.docker.contiki,
            'type': 'bind'
        }

        logger.info("Building a containerized controller")
        self.__contiki_source = config.docker.contiki
        self.__cooja_log = os.path.join(
            self.__contiki_source, config.docker.script_folder, 'COOJA.log')
        self.__testlog = os.path.join(
            self.__contiki_source, config.docker.script_folder, 'COOJA.testlog')
        self.__simulation_folder_container = config.docker.script_folder
        self.__simulation_script = os.path.join(
            self.__contiki_source, config.docker.script_folder, config.docker.simulation_script)
        self.__new_simulation_script = None
        run_simulation_file = '/bin/sh -c '+'"cd ' + \
            self.__simulation_folder_container+' && ./run-cooja.py ' +\
            config.docker.simulation_script + '"'

        # Hack to get the port number
        self.__port = config.docker.port

        # Container
        self.container = CoojaDocker(docker_image=config.docker.image, script=run_simulation_file,
                                     mount=mount, sysctls=sysctls, ports=ports,
                                     privileged=config.docker.privileged,
                                     detach=config.docker.detach, log_file=self.__cooja_log)

        logger.info(f"Contiki source: {self.__contiki_source}")
        logger.info(f"Cooja log: {self.__cooja_log}")
        logger.info(f"Cooja test log: {self.__testlog}")
        logger.info(f"Simulation folder: {self.__simulation_folder_container}")
        logger.info(f"Simulation script: {self.__simulation_script}")

        super().__init__(
            config=config
        )

    # Controller related functions

    def timeout(self):
        sleep(1.2)

    def start(self):
        # We need to overwrite the port of the serial socket in the
        # csc simulation file
        with open(self.__simulation_script, "r") as input_file:
            self.__new_simulation_script = self.__simulation_script.split('.')
            self.__new_simulation_script = "".join(
                [self.__new_simulation_script[0], "-temp.csc"])
            filedata = input_file.read()
            # Replace the target string
            filedata = filedata.replace(str(60001), str(self.__port))
            with open(self.__new_simulation_script, "w") as new_tmp_file:
                new_tmp_file.write(filedata)

        # Overwrite the simulation script
        self.container.script = '/bin/sh -c '+'"cd ' + \
            self.__simulation_folder_container+' && ./run-cooja.py ' + \
            self.__new_simulation_script.split('/')[-1] + '"'
        # logger.info(f"new script: {self.container.script}")

        self.container.start_container()
        super().start()

    def stop(self):
        self.container.shutdown()
        # Delete the tmp simulation csc file if exists
        if self.__new_simulation_script is not None:
            if os.path.exists(self.__new_simulation_script):
                os.remove(self.__new_simulation_script)
        # Delete COOJA.log and COOJA.testlog
        if os.path.exists(self.__cooja_log):
            os.remove(self.__cooja_log)
        if os.path.exists(self.__testlog):
            os.remove(self.__testlog)
        super().stop()

    def reset(self):
        # logger.info('Resetting container, controller, etc.')
        self.stop()
        self.start()
