class FitIoTLABController(BaseController):
    def __init__(
            self,
            socket_host: str = '127.0.0.1',
            socket_port: int = 60001,
            db_name: str = 'mySDN',
            db_host: str = '127.0.0.1',
            db_port: int = 27017,
            simulation_name: str = 'mySimulation',
            processing_window: int = 200,
            max_channel_offsets: int = 3,
            max_slotframe_size: int = 500,
            tsch_scheduler: Optional[str] = 'Contention Free',
            log_dir: str = "./monitor/"):
        super().__init__(
            socket_host,
            socket_port,
            db_name,
            db_host,
            db_port,
            simulation_name,
            processing_window,
            max_channel_offsets,
            max_slotframe_size,
            tsch_scheduler,
            log_dir)

    def start(self):
        print('starting FIT IoT LAB')