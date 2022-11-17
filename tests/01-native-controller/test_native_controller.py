from subprocess import Popen, PIPE
import networkx as nx

import os
import sys

from sdwsn_controller.controller.controller import Controller
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.sink_communication.sink_comm import SinkComm
from sdwsn_controller.tsch.contention_free_scheduler \
    import ContentionFreeScheduler


from rich.logging import RichHandler
import logging.config
import logging.handlers

from time import sleep

logger = logging.getLogger('native_controller')


def run_data_plane(controller):
    logger.info("before reset")
    controller.reset()
    # We now wait until we reach the processing_window
    logger.info("before wait")
    wait = controller.wait()
    assert wait == 1
    # We get the network links, useful when calculating the routing
    logger.info("before links")
    G = controller.get_network_links()
    assert nx.is_empty(G) is False
    # Run the dijkstra algorithm with the current links
    logger.info("before compute routes")
    path = controller.compute_routes(G)
    logger.info(f'paths: {path}')
    assert len(path) != set()
    # Set the slotframe size - (Max # of sensor in WSN is 10)
    slotframe_size = 12
    # We now set the TSCH schedules for the current routing
    logger.info("before computes tsch")
    controller.compute_tsch_schedule(path, slotframe_size)
    links = controller.tsch_scheduler.scheduler_get_list_ts_in_use()
    logger.info(f'links: {links}')
    assert len(links) != 0
    # Send the entire routes
    logger.info("before send routes")
    routes_sent = controller.send_routes()
    assert routes_sent == 1
    # Send the entire TSCH schedule
    logger.info("before send tsch")
    tsch_sent = controller.send_tsch_schedules()
    assert tsch_sent == 1
    # Reset packet sequence
    controller.reset_pkt_sequence()
    # Wait for the network to settle
    logger.info("before wait2")
    wait = controller.wait()
    assert wait == 1


def test_native_controller():
    # -------------------- Create logger --------------------
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
    assert os.getenv('CONTIKI_NG')
    contiki_source = os.getenv('CONTIKI_NG')
    simulation_folder = 'examples/elise'
    python_script = 'cooja-orchestra.csc'
    logger.info("starting native controller")
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

    logger.info('closing controller')

    controller.stop()

    logger.info('closed controller')
    sys.exit()

    # Popen(['netstat', '-vanp', 'tcp', '|', 'grep', '60001'], stdout=PIPE)
    # p2 = Popen(["grep", "LISTEN"], stdin=p1.stdout, stdout=PIPE)
