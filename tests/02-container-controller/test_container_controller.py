#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import networkx as nx

import os

from sdwsn_controller.network.network import Network
from sdwsn_controller.controller.container_controller \
    import ContainerController
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.tsch.contention_free_scheduler \
    import ContentionFreeScheduler


# This number has to be unique across all test
# otherwise, the github actions will fail
# TEST: This might not be necessary anymore.
PORT = 60003


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
    # controller.reset_pkt_sequence()
    # Wait for the network to settle
    wait = controller.wait()
    assert wait == 1


def test_container_controller():
    assert os.getenv('CONTIKI_NG')
    contiki_source = os.getenv('CONTIKI_NG')
    assert os.getenv('DOCKER_BASE_IMG')
    docker_image = os.getenv('DOCKER_BASE_IMG')
    docker_target = '/home/user/contiki-ng'
    # use different port number to avoid interfering with
    # the native controller
    simulation_folder = 'examples/elise'
    simulation_script = 'cooja-orchestra.csc'
    # -------------------- setup controller --------------------
    # Network
    network = Network(processing_window=200,
                      socket_host='127.0.0.1', socket_port=PORT)

    # TSCH scheduler
    tsch_scheduler = ContentionFreeScheduler()

    # Routing algorithm
    routing = Dijkstra()

    controller = ContainerController(
        docker_image=docker_image,
        simulation_script=simulation_script,
        simulation_folder=simulation_folder,
        docker_target=docker_target,
        contiki_source=contiki_source,
        port=PORT,
        # Reward processor
        network=network,
        routing=routing,
        tsch_scheduler=tsch_scheduler
    )
    # --------------------Start data plane ------------------------
    # Let's start the data plane first
    run_data_plane(controller)

    controller.stop()
