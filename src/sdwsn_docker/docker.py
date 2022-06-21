from contextlib import suppress
from typing import Dict, Optional, Tuple
import os
import docker
from docker.types import Mount
from time import sleep


class CoojaDocker():
    def __init__(self, image: str, command: Optional[str] = None,
                 mount: Optional[Dict] = None, sysctls: Optional[Dict] = None,
                 ports: Optional[Dict] = None, privileged: bool = True, detach: bool = True,
                 socket_file: Optional[str] = None) -> None:
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

    def setup_container(self):
        self.container = self.client.containers.run(self.image, command=self.command,
                                                    mounts=[
                                                        self.mount], sysctls=self.sysctls,
                                                    ports=self.ports, privileged=self.privilaged,
                                                    detach=self.detach)
        # self.container.wait(timeout=10)

    def start_container(self):
        self.client.containers.prune()  # Remove previous containers
        self.setup_container()
        sleep(3)

    def cooja_socket_status(self):
        # This method checks whether the socket is currently running in Cooja
        if not os.access(self.socket_file, os.R_OK):
            print('The input file "{}" does not exist'.format(self.socket_file))

        is_listening = False
        is_fatal = False

        with open(self.socket_file, "r") as f:
            contents = f.read()
            read_line = "Listening on port: " + \
                str(self.ports[self.container_port])
            fatal_line = "Exception when loading simulation:"
            is_listening = read_line in contents
            # print(f'listening result: {is_listening}')
            is_fatal = fatal_line in contents
        return is_listening, is_fatal

    def wait_socket_running(self):
        cooja_socket_active, fatal_error = self.cooja_socket_status()

        while cooja_socket_active != True:
            sleep(2)
            cooja_socket_active, fatal_error = self.cooja_socket_status()
            if fatal_error:
                print("Simulation compilation error, starting over ...")
                self.client.containers.prune()  # Remove previous containers
                self.start_container()

        print("Cooja socket interface is up and running")

    def status(self):
        return self.container.status

    def shutdown(self):
        self.container.kill()
