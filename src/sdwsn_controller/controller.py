import threading
from time import sleep
from sdwsn_common import common
from threading import Thread
from abc import ABC, abstractmethod
from sdwsn_serial.serial import SerialBus
from sdwsn_database.database import Database
from sdwsn_packet.packet_dissector import PacketDissector
from typing import Dict, Optional
from sdwsn_docker.docker import CoojaDocker
from sdwsn_result_analysis.run_analysis import run_analysis
from sdwsn_database.database import NODES_INFO

import numpy as np
import networkx as nx


class BaseController(ABC):
    def __init__(
        self,
        cooja_host: str = '127.0.0.1',
        cooja_port: int = 60001,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        simulation_name: str = 'mySimulation',
        processing_window: int = 200
    ):
        # Save instance of a serial interface
        self.ser = SerialBus(cooja_host, cooja_port)
        # Save instance of packet dissector
        self.packet_dissector = PacketDissector(db_name, db_host, db_port)
        # Variable to check whether the controller is running or not
        self.is_running = False
        self.simulation_name = simulation_name
        self.num_episodes = 0
        self.processing_window = processing_window

    def controller_start(self):
        # Initialize database
        self.packet_dissector.initialise_db()
        # Start the serial interface
        self.__controller_serial_start()
        # Restart variables at packet dissector
        self.packet_dissector.cycle_sequence = 0
        self.packet_dissector.sequence = 0
        # Set running flag
        self.is_running = True

    def controller_stop(self):
        # Clear the running flag
        self.is_running = False
        # Stop the serial interface
        self.__controller_serial_stop()
        # Reset the packet dissector sequence
        self.packet_dissector.cycle_sequence = 0
        self.packet_dissector.sequence = 0
        # Run the data analysis script if there is data in the DB
        self.run_data_analysis()

    def run_data_analysis(self):
        self.num_episodes += 1
        # This function plots and save the charts in pdf format
        if self.packet_dissector.DATABASE is not None:
            run_analysis(self.packet_dissector,
                         self.simulation_name+str(self.num_episodes))

    def __controller_serial_stop(self):
        self.ser.shutdown()

    """ Serial/socket interface functions """

    def __controller_serial_start(self):
        # Connect serial
        if self.ser.connect() != 0:
            print('unsuccessful serial connection')
            return 0
        print("Socket up and running")
        # Read serial
        self._read_ser_thread = threading.Thread(target=self.__read_ser)
        self._read_ser_thread.start()
        return 1

    def __read_ser(self):
        while(1):
            try:
                msg = self.ser.recv(0.1)
                if(len(msg) > 0):
                    self.packet_dissector.handle_serial_packet(msg)
                if not self.is_running:
                    break
            except TypeError:
                pass

    """ Cycle management """

    def controller_wait_cycle_finishes(self):
        while(1):
            if self.packet_dissector.sequence > self.processing_window:
                break
            sleep(1)
        print("cycle finished")

    """ Network information methods """

    def controller_get_network_links(self):
        # Get last index of sensor
        N = self.packet_dissector.get_last_index_wsn()+1
        # Neighbor matrix
        nbr_rssi_matrix = np.zeros(shape=(N, N))
        # We first loop through all sensor nodes
        nodes = self.packet_dissector.find(NODES_INFO, {})
        for node in nodes:
            # Get last neighbors
            nbr = self.packet_dissector.get_last_nbr(node["node_id"])
            if nbr is not None:
                for nbr_node in nbr:
                    source, _ = node["node_id"].split('.')
                    dst, _ = nbr_node["dst"].split('.')
                    nbr_rssi_matrix[int(source)][int(
                        dst)] = int(nbr_node["rssi"])
        matrix = nbr_rssi_matrix * -1
        G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
        G.remove_nodes_from(list(nx.isolates(G)))
        return G

    """ Routing functions """

    def compute_dijkstra(self, G, routes):
        # TODO: Routes should be part of the controller
        # We want to compute the SP from all nodes to the controller
        path = {}
        for node in list(G.nodes):
            if node != 1 and node != 0:
                print("sp from node "+str(node))
                try:
                    node_path = nx.dijkstra_path(G, node, 1, weight='weight')
                    print("dijkstra path")
                    print(node_path)
                    path[node] = node_path
                    # TODO: find a way to avoid forcing the last addr of
                    # sensor nodes to 0.
                    routes.add_route(
                        str(node)+".0", "1.1", str(node_path[1])+".0")
                except nx.NetworkXNoPath:
                    print("path not found")
        routes.print_routes()
        print("total path")
        print(path)
        return path

    """ Sequence functions """

    def increase_cycle_sequence(self):
        self.packet_dissector.cycle_sequence += 1

    def increase_pkt_sequence(self):
        self.packet_dissector.sequence += 1

    def reset_pkt_sequence(self):
        self.packet_dissector.sequence = 0

    def get_cycle_sequence(self):
        return self.packet_dissector.cycle_sequence

    def controller_send_data(self, data):
        if self.is_running:
            print("sending serial packet")
            # Send data to the serial send interface
            self.ser.send(data)
        else:
            print("Couldn't send data, controller is Not running")

    def controller_reliable_send(self, data, ack):
        # Reliable data transmission
        # set retransmission
        rtx = 0
        # Send NC packet through serial interface
        self.controller_send_data(data)
        # Result variable to see if the sending went well
        result = 0
        while True:
            if (self.packet_dissector.ack_pkt.reserved0 == ack):
                print("correct ACK received")
                result = 1
                break
            print("ACK not received")
            # We stop sending the current NC packet if
            # we reached the max RTx or we received ACK
            if(rtx >= 7):
                print("ACK never received")
                break
            # We resend the packet if retransmission < 7
            rtx = rtx + 1
            self.controller_send_data(data)
            sleep(1.2)
        return result


class ContainerController(BaseController):
    def __init__(
            self,
            image: str = 'contiker/contiki-ng',
            command: str = '/bin/sh -c "cd examples/benchmarks/rl-sdwsn && ./run-cooja.py"',
            mount: Dict = {
                'target': '/home/user/contiki-ng',
                'source': '/Users/fernando/contiki-ng',
                'type': 'bind'
            },
            sysctls: Dict = {
                'net.ipv6.conf.all.disable_ipv6': 0
            },
            container_ports: Dict = {
                'container': 60001,
                'host': 60001
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
            processing_window: int = 200
    ):
        super().__init__(
            cooja_host,
            cooja_port,
            db_name,
            db_host,
            db_port,
            simulation_name,
            processing_window)

        self.container = CoojaDocker(image=image, command=command, mount=mount,
                                     sysctls=sysctls, ports=container_ports, privileged=privileged, detach=detach,
                                     socket_file=socket_file)

    def container_controller_start(self):
        self.container.start_container()
        self.controller_start()

    def container_controller_shutdown(self):
        self.controller_stop()
        self.container.shutdown()

    def container_reset(self):
        print('Resetting container, controller, etc.')
        self.container_controller_shutdown()
        self.container_controller_start()
