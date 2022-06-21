from contextlib import suppress
from typing import Dict, Optional, Tuple
import os
import docker
from docker.errors import DockerException
from docker.types import Mount
from requests.exceptions import ReadTimeout


def cooja_socket_status(file, port):
    # This method checks whether the socket is currently running in Cooja
    input_file = file
    if not os.access(input_file, os.R_OK):
        print('The input file "{}" does not exist'.format(input_file))

    is_listening = False
    is_fatal = False

    with open(input_file, "r") as f:
        contents = f.read()
        read_line = "Listening on port: "+str(port)
        fatal_line = "Exception when loading simulation:"
        is_listening = read_line in contents
        # print(f'listening result: {is_listening}')
        is_fatal = fatal_line in contents
    return is_listening, is_fatal


class CoojaDocker():
    def __init__(self, image: str, command: Optional[str] = None,
                 mount: Optional[Dict] = None, sysctls: Optional[Dict] = None,
                 ports: Optional[Dict] = None, privileged: bool = True, detach: bool = True) -> None:
        self.image = image
        self.command = command
        self.mount = Mount(
            mount['target'], mount['source'], type=mount['type'])
        self.sysctls = sysctls
        container_port = str(ports['container'])+'/tcp'
        self.ports = {container_port: ports['host']}
        self.privilaged = privileged
        self.detach = detach
        self.client = docker.from_env()
        self.container = None

    def run(self):
        self.container = self.client.containers.run(self.image, command=self.command,
                                                    mounts=[
                                                        self.mount], sysctls=self.sysctls,
                                                    ports=self.ports, privileged=self.privilaged,
                                                    detach=self.detach)
        # self.container.wait(timeout=10)

    def status(self):
        return self.container.status

    def shutdown(self):
        self.container.kill()
