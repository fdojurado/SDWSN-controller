from sdwsn_controller.controller.common_controller import CommonController
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler


class FitIoTLABController(CommonController):
    def __init__(
        self,
        socket_port: int = 2001,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        processing_window: int = 200,
        tsch_scheduler: object = ContentionFreeScheduler(500, 3)
    ):
        super().__init__(
            port=socket_port,
            db_name=db_name,
            db_host=db_host,
            db_port=db_port,
            processing_window=processing_window,
            tsch_scheduler=tsch_scheduler,
        )

    def fit_iot_lab_start(self):
        print('starting FIT IoT LAB controller')
        # Initialize main controller
        self.start()

    def fit_iot_lab_stop(self):
        print('starting FIT IoT LAB controller')
        # Stop main controller
        self.stop()

    def fit_iot_lab_reset(self):
        print('Resetting FIT IoT LAB controller')
        self.fit_iot_lab_stop()
        self.fit_iot_lab_start()
