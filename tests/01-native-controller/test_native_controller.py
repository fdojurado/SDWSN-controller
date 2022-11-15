import logging

import os

from rich.logging import RichHandler

from sdwsn_controller.controller.controller import Controller
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.sink_communication.sink_comm import SinkComm
from sdwsn_controller.tsch.contention_free_scheduler \
    import ContentionFreeScheduler


def run_data_plane(controller):
    controller.reset()
    # We now wait until we reach the processing_window
    controller.wait()
    # We get the network links, useful when calculating the routing
    G = controller.get_network_links()
    # Run the dijkstra algorithm with the current links
    path = controller.compute_routes(G)
    # Set the slotframe size - (Max # of sensor in WSN is 10)
    slotframe_size = 12
    # We now set the TSCH schedules for the current routing
    controller.compute_tsch_schedule(path, slotframe_size)
    # Send the entire routes
    controller.send_routes()
    # Send the entire TSCH schedule
    controller.send_tsch_schedules()
    # Reset packet sequence
    controller.reset_pkt_sequence()
    # Wait for the network to settle
    controller.wait()


def test_native_controller():
    assert os.getenv('CONTIKI_NG')
    contiki_source = os.getenv('CONTIKI_NG')
    simulation_folder = 'examples/elise'
    python_script = 'cooja-orchestra.csc'
    # -------------------- Create logger --------------------
    logger = logging.getLogger('main')

    formatter = logging.Formatter(
        '%(asctime)s - %(message)s')
    logger.setLevel(logging.DEBUG)

    stream_handler = RichHandler(rich_tracebacks=True)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logFilePath = "my.log"
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s |  %(levelname)s: %(message)s')
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=logFilePath, when='midnight', backupCount=30)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    # -------------------- setup controller --------------------
    # Socket
    socket = SinkComm()

    # TSCH scheduler
    tsch_scheduler = ContentionFreeScheduler()

    # Database
    db = DatabaseManager()

    # Routing algorithm
    routing = Dijkstra()

    # Packet dissector
    packet_dissector = PacketDissector(database=db)

    controller = Controller(
        # Controller related
        contiki_source=contiki_source,
        simulation_folder=simulation_folder,
        simulation_script=python_script,
        # Database
        db=db,
        # socket
        socket=socket,
        # Packet dissector
        packet_dissector=packet_dissector,
        processing_window=200,
        router=routing,
        tsch_scheduler=tsch_scheduler
    )
    # --------------------Start data plane ------------------------
    # Let's start the data plane first
    run_data_plane(controller)

    controller.stop()
