from contextlib import suppress
from typing import Dict, Optional, Tuple

import docker
from docker.errors import DockerException
from docker.types import Mount
from requests.exceptions import ReadTimeout


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

    def status(self):
        return self.container.status

    def shutdown(self):
        self.container.kill()
