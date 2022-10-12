from sdwsn_controller.controller.common_controller import CommonController
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler

from time import sleep

from rich.progress import Progress
import logging

logger = logging.getLogger(__name__)

class FitIoTLABController(CommonController):
    def __init__(
        self,
        socket_port: int = 2001,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        processing_window: int = 200,
        tsch_scheduler: object = ContentionFreeScheduler(500, 3),
        power_norm_offset: float = 0.0,
        delay_norm_offset: float = 0.0,
        reliability_norm_offset: float = 0.0
    ):
        super().__init__(
            port=socket_port,
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            tsch_scheduler=tsch_scheduler,
            power_norm_offset=power_norm_offset,
            delay_norm_offset=delay_norm_offset,
            reliability_norm_offset=reliability_norm_offset
        )

        self.__processing_window = processing_window

    """ Controller functions not implemented in the common controller """

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
            sleep(10)
        return result

    def wait(self):
        """
         We wait for the current cycle to finish
         """
        # If we have not received any data after looping 10 times
        # We return
        logger.info("Waiting for the current cycle, in the FIT IoT LAB, to finish")
        result = -1
        while(1):
            if self.sequence > self.__processing_window:
                result = 1
                break
            sleep(1)
        logger.info(f"cycle finished, result: {result}")
        return result

    def fit_iot_lab_start(self):
        sleep(10)
        logger.info('starting FIT IoT LAB controller')
        # Initialize main controller
        self.start()

    def fit_iot_lab_stop(self):
        logger.info('stopping FIT IoT LAB controller')
        # Stop main controller
        self.stop()

    def reset(self):
        logger.info('Resetting FIT IoT LAB controller')
        self.fit_iot_lab_stop()
        self.fit_iot_lab_start()
