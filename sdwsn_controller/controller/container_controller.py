from sdwsn_controller.controller.common_controller import CommonController
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.docker.docker import CoojaDocker
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.routing.dijkstra import Dijkstra

from rich.progress import Progress
from typing import Dict
from time import sleep
import logging

logger = logging.getLogger('main.'+__name__)


class ContainerController(CommonController):
    def __init__(
        self,
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
        cooja_host: str = '127.0.0.1',
        cooja_port: int = 60001,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        simulation_name: str = 'mySimulation',
        processing_window: int = 200,
        router: object = Dijkstra(),
        tsch_scheduler: object = ContentionFreeScheduler(500, 3)
    ):
        container_ports = {
            'container': cooja_port,
            'host': cooja_port
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
        logger.info(f'cooja port: {cooja_port}')
        logger.info(f'DB name: {db_name}')
        logger.info(f'simulation name: {simulation_name}')

        self.container = CoojaDocker(image=image, command=command, mount=mount,
                                     sysctls=sysctls, ports=container_ports, privileged=privileged, detach=detach,
                                     socket_file=socket_file)

        self.__processing_window = processing_window

        super().__init__(
            host=cooja_host,
            port=cooja_port,
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            tsch_scheduler=tsch_scheduler,
            router=router
        )

    """ 
        Controller related functions
    """

    def reliable_send(self, data, ack):
        # Reliable socket data transmission
        # set retransmission
        rtx = 0
        # Send NC packet through serial interface
        self.send(data)
        # Result variable to see if the sending went well
        result = 0
        while True:
            if self.packet_dissector.ack_pkt is not None:
                if (self.packet_dissector.ack_pkt.reserved0 == ack):
                    logger.debug("correct ACK received")
                    result = 1
                    break
                logger.debug("ACK not received")
                # We stop sending the current NC packet if
                # we reached the max RTx or we received ACK
                if(rtx >= 7):
                    logger.warning("ACK never received")
                    break
                # We resend the packet if retransmission < 7
                rtx = rtx + 1
                self.send(data)
            sleep(1.2)
        return result

    def wait(self):
        """
         We wait for the current cycle to finish
         """
        # If we have not received any data after looping 10 times
        # We return
        logger.info(f"Starting new cycle")

        result = -1

        with Progress(transient=True) as progress:
            task1 = progress.add_task(
                "[red]Waiting for the current cycle to finish...", total=self.__processing_window)

            while not progress.finished:
                progress.update(task1, completed=self.sequence)
                if self.sequence >= self.__processing_window:
                    result = 1
                    logger.info(f"Cycle completed")
                    progress.update(task1, completed=100)
                sleep(0.1)

        # # count = 0
        # result = -1
        # while(1):
        #     # count += 1
        #     if self.sequence > self.__processing_window:
        #         result = 1
        #         break
        #     # if count > 10:
        #     #     result = 0
        #     #     break
        #     # sleep(1)
        logger.info(f"cycle finished, result: {result}")
        return result

    def container_controller_start(self):
        self.container.start_container()
        # Initialize main controller
        self.start()

    def container_controller_stop(self):
        self.container.shutdown()
        # Stop main controller
        self.stop()

    def reset(self):
        logger.info('Resetting container, controller, etc.')
        self.container_controller_stop()
        self.container_controller_start()
