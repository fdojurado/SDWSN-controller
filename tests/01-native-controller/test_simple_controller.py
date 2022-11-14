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

from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.controller.container_controller import ContainerController
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.sink_communication.sink_comm import SinkComm
from rich.logging import RichHandler
import logging.config
import sys

DOCKER_IMAGE = 'contiker/contiki-ng'
SIMULATION_FOLDER = 'examples/elise'
DOCKER_TARGET = '/home/user/contiki-ng'
CONTIKI_SOURCE = '/Users/ffjla/contiki-ng'
PYTHON_SCRIPT = './run-cooja.py cooja-orchestra.csc'


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


def main():

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
    # Script that run inside the container - simulation file as argument
    run_simulation_file = '/bin/sh -c '+'"cd ' + \
        SIMULATION_FOLDER+' && ' + PYTHON_SCRIPT + '"'

    # Socket
    socket = SinkComm()

    # TSCH scheduler
    tsch_scheduler = ContentionFreeScheduler()

    # Database
    db = DatabaseManager()

    # Routing algorithm
    routing = Dijkstra()

    controller = ContainerController(
        docker_image=DOCKER_IMAGE,
        script=run_simulation_file,
        docker_target=DOCKER_TARGET,
        contiki_source=CONTIKI_SOURCE,
        log_file=CONTIKI_SOURCE + '/' + SIMULATION_FOLDER + '/COOJA.log',
        # Database
        db=db,
        # socket
        socket=socket,
        # Packet dissector
        packet_dissector=PacketDissector(database=db),
        processing_window=200,
        router=routing,
        tsch_scheduler=tsch_scheduler
    )
    # --------------------Start data plane ------------------------
    # Let's start the data plane first
    run_data_plane(controller)

    logger.info('done, exiting.')

    controller.stop()

    return


if __name__ == '__main__':
    main()
    sys.exit(0)
