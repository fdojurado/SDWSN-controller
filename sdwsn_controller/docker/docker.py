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

import docker
from docker.types import Mount

import logging

import os

from rich.progress import Progress

from time import sleep
from typing import Dict, Optional

logger = logging.getLogger(f'main.{__name__}')


class CoojaDocker():
    def __init__(
        self,
        docker_image: str = 'contiker/contiki-ng',
        script: str = '/bin/sh -c "cd examples/elise && ./run-cooja.py"',
        mount: Optional[Dict] = None,
        sysctls: Optional[Dict] = None,
        ports: Optional[Dict] = None,
        privileged: bool = True,
        detach: bool = True,
        log_file: Optional[str] = None
    ):
        """
        This runs Cooja within Docker.

        Args:
            docker_image (str, optional): Docker image name. Defaults to 'contiker/contiki-ng'.
            script (str, optional): Command to run the simulation script. Defaults to  \
                '/bin/sh -c "cd examples/elise && ./run-cooja.py"'.
            mount (Optional[Dict], optional): Specification for mounts to be added to the container. Defaults to None.
            sysctls (Optional[Dict], optional): Kernel parameters to set in the container. Defaults to None.
            ports (Optional[Dict], optional): Ports to bind inside the container. Defaults to None.
            privileged (bool, optional): Give extended privileges to this container. Defaults to True.
            detach (bool, optional): Run container in the background. Defaults to True.
            log_file (Optional[str], optional): Path to the 'COOJA.log' file. Defaults to None.
        """
        assert isinstance(docker_image, str)
        assert isinstance(script, str)
        assert isinstance(mount, Dict)
        assert isinstance(sysctls, Dict)
        assert isinstance(ports, Dict)
        assert isinstance(privileged, bool)
        assert isinstance(detach, bool)
        assert isinstance(log_file, str)

        self.docker_image = docker_image
        self.script = script
        self.mount = Mount(
            mount['target'], mount['source'], type=mount['type'])
        self.sysctls = sysctls
        self.container_port = str(ports['container'])+'/tcp'
        self.ports = {self.container_port: ports['host']}
        self.privilaged = privileged
        self.detach = detach
        self.client = docker.from_env()
        self.container = None
        self.log_file = log_file

        logger.info(f"docker_image: {self.docker_image}")
        logger.info(f"script: {self.script}")
        logger.info(f"Mount target: {mount['target']}")
        logger.info(f"Mount source: {mount['source']}")
        logger.info(f"Mount type: {mount['type']}")
        logger.info(f'sysctls: {self.sysctls}')
        logger.info(f'Container port: {self.container_port}')
        logger.info(f'Ports: {self.ports }')
        logger.info(f'detach: {self.detach }')
        logger.info(f'log_file: {self.log_file}')

    def __run_container(self):
        logger.info("Starting container")
        self.container = self.client.containers.run(self.docker_image, command=self.script,
                                                    mounts=[
                                                        self.mount], sysctls=self.sysctls,
                                                    ports=self.ports, privileged=self.privilaged,
                                                    detach=self.detach)
        # self.container.wait(timeout=10)

    def start_container(self):
        # self.client.containers.prune()  # Remove previous containers
        self.__run_container()
        sleep(2)
        status = 0
        with Progress(transient=True) as progress:
            task1 = progress.add_task(
                "[red]Waiting for Cooja to start...", total=300)

            while not progress.finished:
                progress.update(task1, advance=1)
                if os.access(self.log_file, os.R_OK):
                    status = 1
                    progress.update(task1, completed=300)
                sleep(1)

        if status == 0:
            raise Exception("Failed to start Cooja.")

        self.__wait_socket_running()

    def __cooja_socket_status(self):
        # This method checks whether the socket is currently running in Cooja
        if not os.access(self.log_file, os.R_OK):
            logger.warning(
                'The input file "{}" does not exist'.format(self.log_file))

        is_listening = False
        is_fatal = False

        with open(self.log_file, "r") as f:
            contents = f.read()
            read_line = "Listening on port: " + \
                str(self.ports[self.container_port])
            fatal_line = "Simulation not loaded"
            is_listening = read_line in contents
            # logger.info(f'listening result: {is_listening}')
            is_fatal = fatal_line in contents
        return is_listening, is_fatal

    def __wait_socket_running(self):
        cooja_socket_active, fatal_error = self.__cooja_socket_status()
        status = 0
        with Progress(transient=True) as progress:
            task1 = progress.add_task(
                "[red]Setting up Cooja simulation...", total=300)
            while not progress.finished:
                progress.update(task1, advance=1)
                cooja_socket_active, fatal_error = self.__cooja_socket_status()
                if fatal_error:
                    logger.warning(
                        "Simulation compilation error, starting over ...")
                    # self.client.containers.prune()  # Remove previous containers
                    self.start_container()
                if cooja_socket_active:
                    status = 1
                    progress.update(task1, completed=300)

                sleep(1)

        if status == 0:
            raise Exception("Failed to start the simulation.")

        logger.info("Cooja socket interface is up and running")

    def status(self):
        return self.container.status

    def shutdown(self):
        if self.container:
            self.container.stop()
