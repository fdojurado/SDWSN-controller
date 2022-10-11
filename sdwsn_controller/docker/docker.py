from contextlib import suppress
from typing import Dict, Optional, Tuple
import os
import docker
from docker.types import Mount
from time import sleep
from rich.progress import Progress
import logging

logger = logging.getLogger(__name__)


class CoojaDocker():
    def __init__(
        self,
        image: str,
        command: str = None,
        mount: Optional[Dict] = None,
        sysctls: Optional[Dict] = None,
        ports: Optional[Dict] = None,
        privileged: bool = True,
        detach: bool = True,
        socket_file: Optional[str] = None
    ):
        self.image = image
        self.command = command
        self.mount = Mount(
            mount['target'], mount['source'], type=mount['type'])
        self.sysctls = sysctls
        self.container_port = str(ports['container'])+'/tcp'
        self.ports = {self.container_port: ports['host']}
        self.privilaged = privileged
        self.detach = detach
        self.client = docker.from_env()
        self.container = None
        self.socket_file = socket_file

    def __run_container(self):
        logger.info("Starting container")
        self.container = self.client.containers.run(self.image, command=self.command,
                                                    mounts=[
                                                        self.mount], sysctls=self.sysctls,
                                                    ports=self.ports, privileged=self.privilaged,
                                                    detach=self.detach)
        # self.container.wait(timeout=10)

    def start_container(self):
        # self.client.containers.prune()  # Remove previous containers
        self.__run_container()

        sleep(2)

        with Progress(transient=True) as progress:
            task1 = progress.add_task(
                "[red]Waiting for Cooja to start...", total=100)

            while not progress.finished:
                progress.update(task1, advance=0.1)
                if os.access(self.socket_file, os.R_OK):
                    progress.update(task1, completed=100)
                sleep(0.1)

        self.__wait_socket_running()

    def __cooja_socket_status(self):
        # This method checks whether the socket is currently running in Cooja
        if not os.access(self.socket_file, os.R_OK):
            logger.warning(
                'The input file "{}" does not exist'.format(self.socket_file))

        is_listening = False
        is_fatal = False

        with open(self.socket_file, "r") as f:
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

        with Progress(transient=True) as progress:
            task1 = progress.add_task(
                "[red]Setting up Cooja simulation...", total=10)
            while not progress.finished:
                progress.update(task1, advance=0.1)
                cooja_socket_active, fatal_error = self.__cooja_socket_status()
                if fatal_error:
                    logger.warning(
                        "Simulation compilation error, starting over ...")
                    # self.client.containers.prune()  # Remove previous containers
                    self.start_container()
                if cooja_socket_active == True:
                    progress.update(task1, completed=10)

                sleep(2)

        logger.info("Cooja socket interface is up and running")

    def status(self):
        return self.container.status

    def shutdown(self):
        if self.container:
            self.container.stop()
