import networkx as nx

import os

from sdwsn_controller.controller.container_controller \
    import ContainerController
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.sink_communication.sink_comm import SinkComm
from sdwsn_controller.tsch.contention_free_scheduler \
    import ContentionFreeScheduler


def run_data_plane(controller):
    controller.reset()
    # We now wait until we reach the processing_window
    wait = controller.wait()
    assert wait == 1
    # We get the network links, useful when calculating the routing
    G = controller.get_network_links()
    assert nx.is_empty(G) is False
    # Run the dijkstra algorithm with the current links
    path = controller.compute_routes(G)
    assert len(path) != set()
    # Set the slotframe size - (Max # of sensor in WSN is 10)
    slotframe_size = 12
    # We now set the TSCH schedules for the current routing
    controller.compute_tsch_schedule(path, slotframe_size)
    links = controller.tsch_scheduler.scheduler_get_list_ts_in_use()
    assert len(links) != 0
    # Send the entire routes
    routes_sent = controller.send_routes()
    assert routes_sent == 1
    # Send the entire TSCH schedule
    tsch_sent = controller.send_tsch_schedules()
    assert tsch_sent == 1
    # Reset packet sequence
    controller.reset_pkt_sequence()
    # Wait for the network to settle
    wait = controller.wait()
    assert wait == 1


def test_native_controller():
    assert os.getenv('CONTIKI_NG')
    contiki_source = os.getenv('CONTIKI_NG')
    assert os.getenv('DOCKER_BASE_IMG')
    docker_image = os.getenv('DOCKER_BASE_IMG')
    docker_target = '/home/user/contiki-ng'
    # use different port number to avoid interfering with
    # the native controller
    port = 60020
    simulation_folder = 'examples/elise'
    python_script = './run-cooja.py cooja-orchestra.csc'
    # -------------------- setup controller --------------------
    # Script that run inside the container - simulation file as argument
    run_simulation_file = '/bin/sh -c '+'"cd ' + \
        simulation_folder+' && ' + python_script + '"'

    # Socket
    socket = SinkComm(port=port)

    # TSCH scheduler
    tsch_scheduler = ContentionFreeScheduler()

    # Database
    db = DatabaseManager()

    # Routing algorithm
    routing = Dijkstra()

    # Packet dissector
    packet_dissector = PacketDissector(database=db)

    controller = ContainerController(
        docker_image=docker_image,
        port=port,
        script=run_simulation_file,
        docker_target=docker_target,
        contiki_source=contiki_source,
        log_file=contiki_source + '/' + simulation_folder + '/COOJA.log',
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
