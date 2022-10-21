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

from sdwsn_controller.controller.controller import BaseController
from sdwsn_controller.common import common
from sdwsn_controller.packet.packet import RA_Packet_Payload
from sdwsn_controller.routing.dijkstra import Dijkstra
from sdwsn_controller.database.db_manager import DatabaseManager
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.serial.serial import SerialBus
from sdwsn_controller.packet.packet_dissector import PacketDissector
from sdwsn_controller.reinforcement_learning.reward_processing import EmulatedRewardProcessing
from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.packet.packet import Cell_Packet_Payload
from sdwsn_controller.database.db_manager import SLOT_DURATION
from sdwsn_controller.database.database import OBSERVATIONS


import numpy as np
import networkx as nx
import threading
from time import sleep
import logging

logger = logging.getLogger('main.'+__name__)


class CommonController(BaseController):
    """
    A type of controller that shares functionalities with simulated and
     real-world deployments; but not with numerical controllers.

    Args:
        alpha (float): Coefficient for avg power consumption.
        beta (float): Coefficient for avg delay.
        delta (float): Coefficient for avg reliability.
        host (str): Host address of the serial interface (Communication with the sink.)
        port (int): Port to stablish the connection with the host. (Communication with the sink.)
        db_name (str): The name of the database.
        db_host (str): Address of the machine hosting the data base.
        db_port (int): Port of the database.
        router (object): The routing algorithm.
        tsch_scheduler (object): The TSCH scheduler.
        power_min (int): Minimum power consumption - useful in the normalization. (RL)
        power_max (int): Maximum power consumption - useful in the normalization. (RL)
        delay_min (int): Minimum delay - useful in the normalization. (RL)
        delay_max (int): Maximum delay - useful in the normalization. (RL)
        power_norm_offset (float): Power normalization offset - this is to balance/ease the training of the RL alg.
        delay_norm_offset (float): Delay normalization offset - this is to balance/ease the training of the RL alg.
        reliability_norm_offset (float): Reliability normalization offset - this is to balance/ease the training of the RL alg.
    """

    def __init__(
        self,
        alpha: float = None,
        beta: float = None,
        delta: float = None,
        host: str = '127.0.0.1',
        port: int = 60001,
        db_name: str = 'mySDN',
        db_host: str = '127.0.0.1',
        db_port: int = 27017,
        router: object = Dijkstra(),
        tsch_scheduler: object = ContentionFreeScheduler(500, 3),
        power_min: int = 0,
        power_max: int = 5000,
        delay_min: int = SLOT_DURATION,
        delay_max: int = 15000,
        power_norm_offset: float = 0.0,
        delay_norm_offset: float = 0.0,
        reliability_norm_offset: float = 0.0
    ):
        # Create a socket communication
        self.__socket = SerialBus(host, port)
        self.__read_socket_thread = None

        # Create database
        self.__db = DatabaseManager(
            name=db_name,
            host=db_host,
            port=db_port
        )

        # Create packet dissector
        self.__packet_dissector = PacketDissector(database=self.__db)

        # Create reward module
        self.__reward_processing = EmulatedRewardProcessing(
            database=self.__db,
            power_min=power_min,
            power_max=power_max,
            delay_min=delay_min,
            delay_max=delay_max,
            power_norm_offset=power_norm_offset,
            delay_norm_offset=delay_norm_offset,
            reliability_norm_offset=reliability_norm_offset
        )

        # Create TSCH scheduler module
        self.__tsch_scheduler = tsch_scheduler

        # Create the routing algorithm module
        self.__router = router

        # Initialize some variables
        self.__is_running = False

        # Initialize observation variables
        self.timestamp = 0
        self.__alpha = alpha
        self.__beta = beta
        self.__delta = delta
        self.power_wam = 0
        self.power_mean = 0
        self.power_normalized = 0
        self.delay_wam = 0
        self.delay_mean = 0
        self.delay_normalized = 0
        self.pdr_wam = 0
        self.pdr_mean = 0
        self.__current_slotframe_size = 0
        self.__last_tsch_link = 0
        self.reward = 0

        super().__init__()

    """ 
        Class related functions 
    """

    def update_observations(self, timestamp, alpha, beta, delta, power_wam, power_mean,
                            power_normalized, delay_wam, delay_mean, delay_normalized,
                            pdr_wam, pdr_mean, current_sf_len, last_ts_in_schedule, reward):
        self.timestamp = timestamp
        self.user_requirements = (alpha, beta, delta)
        self.power_wam = power_wam
        self.power_mean = power_mean
        self.power_normalized = power_normalized
        self.delay_wam = delay_wam
        self.delay_mean = delay_mean
        self.delay_normalized = delay_normalized
        self.pdr_wam = pdr_wam
        self.pdr_mean = pdr_mean
        self.current_slotframe_size = current_sf_len
        self.last_tsch_link = last_ts_in_schedule
        self.reward = reward

    """ Controller related functions """

    def start(self):
        # Initialize database
        self.init_db()
        # Start the socket interface
        sock = self.comm_interface_start()
        if sock == 0:
            self.stop()
            return
        # Restart variables at packet dissector
        self.cycle_sequence = 0
        self.sequence = 0
        # Set running flag
        self.__is_running = True
        # self.controller_start()

    def stop(self):
        # Clear the running flag
        self.__is_running = False
        # Stop the serial interface
        self.comm_interface_stop()
        # Reset the packet dissector sequence
        self.cycle_sequence = 0
        self.sequence = 0
        # Run the data analysis script if there is data in the DB
        # self.run_data_analysis()

    def wait_seconds(self, seconds):
        sleep(seconds)

    def send(self, data):
        if self.__is_running:
            # Send data to the serial send interface
            self.__socket.send(data)
        else:
            logger.warning("Couldn't send data, controller is Not running")

    """ Packet dissector related functionalities """

    @property
    def packet_dissector(self):
        return self.__packet_dissector

    @property
    def sequence(self):
        return self.__packet_dissector.sequence

    @sequence.setter
    def sequence(self, num):
        self.__packet_dissector.sequence = num

    @property
    def cycle_sequence(self):
        return self.__packet_dissector.cycle_sequence

    @cycle_sequence.setter
    def cycle_sequence(self, num):
        self.__packet_dissector.cycle_sequence = num

    def increase_sequence(self):
        self.sequence += 1
        return self.sequence

    def increase_cycle_sequence(self):
        self.cycle_sequence += 1
        return self.cycle_sequence

    def reset_pkt_sequence(self):
        self.sequence = 0

    def get_cycle_sequence(self):
        return self.cycle_sequence

    """
    Serial interface methods:
        * Start
        * Stop
        * read
    """

    def comm_interface_start(self):
        # Connect serial
        if self.__socket.connect() != 0:
            logger.warning(
                f'unsuccessful serial connection (host:{self.__socket.host}, port: {self.__socket.port})')
            return 0
        logger.info("Socket up and running")
        # Read serial
        self.__read_socket_thread = threading.Thread(
            target=self.comm_interface_read)
        self.__read_socket_thread.start()
        return 1

    def comm_interface_stop(self):
        if self.__read_socket_thread is not None:
            logger.info(
                f"start to shutdown thread, running flag = {self.__is_running}")
            self.__read_socket_thread.join()
        self.__socket.shutdown()

    def comm_interface_read(self):
        while(1):
            try:
                msg = self.__socket.recv(0.1)
                if(len(msg) > 0):
                    self.packet_dissector.handle_serial_packet(msg)
            except TypeError:
                pass
            if not self.__is_running:
                break
        logger.info("Socket reading thread exited.")

    """ Database related functionalities """

    def init_db(self):
        self.__db.initialize()

    @property
    def db(self):
        return self.__db

    def delete_info_collection(self):
        self.db.delete_collection(NODES_INFO)

    def export_db(self, simulation_name, folder):
        self.db.export_collection(OBSERVATIONS, simulation_name, folder)

    def get_network_links(self):
        # Get last index of sensor
        N = self.db.get_last_index_wsn()+1
        # Neighbor matrix
        nbr_rssi_matrix = np.zeros(shape=(N, N))
        # We first loop through all sensor nodes
        nodes = self.db.find(NODES_INFO, {})
        for node in nodes:
            # Get last neighbors
            nbr = self.db.get_last_nbr(node["node_id"])
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

    """ TSCH related functionalities """

    def last_active_tsch_slot(self):
        return self.tsch_scheduler.schedule_last_active_ts()

    def compute_tsch_schedule(self, path, current_sf_size):
        # We clean previous schedule first
        self.tsch_scheduler.schedule_clear_schedule()
        self.tsch_scheduler.run(path, current_sf_size)

    @property
    def tsch_scheduler(self):
        return self.__tsch_scheduler

    def send_tsch_schedules(self):
        logger.info("Sending TSCH packet")
        num_pkts = 0
        payload = []
        rows, cols = (self.tsch_scheduler.schedule_max_number_channels,
                      self.tsch_scheduler.schedule_max_number_timeslots)
        for i in range(rows):
            for j in range(cols):
                if (self.tsch_scheduler.schedule_get_schedule(i, j)):
                    for elem in self.tsch_scheduler.schedule_get_schedule(i, j):
                        channel = elem.channeloffset
                        timeslot = elem.timeoffset
                        addr = elem.source
                        type = elem.type
                        dst = elem.destination
                        data = {"channel": channel, "timeslot": timeslot, "addr": addr, "type": type,
                                "dest": dst}
                        logger.debug("schedule element")
                        logger.debug(data)
                        # if num_links < 11:
                        cell_pkt = Cell_Packet_Payload(payload=payload, type=int(type),
                                                       channel=int(channel), timeslot=int(timeslot), scr=addr,
                                                       dst=dst)
                        cell_packed = cell_pkt.pack()
                        payload = cell_packed
                        if len(payload) > 90:
                            logger.debug(f'Sending schedule packet {num_pkts}')
                            # We send the current payload
                            num_pkts += 1
                            current_sf_size = 0
                            if num_pkts == 1:
                                current_sf_size = self.tsch_scheduler.schedule_slot_frame_size
                            packedData, serial_pkt = common.tsch_build_pkt(
                                payload, current_sf_size, self.increase_cycle_sequence())
                            payload = []
                            # Send NC packet
                            self.reliable_send(
                                packedData, serial_pkt.reserved0+1)
        # Send the remain payload if there is one
        if payload:
            num_pkts += 1
            logger.debug(f'Sending schedule packet {num_pkts}')
            current_sf_size = 0
            if num_pkts == 1:
                current_sf_size = self.tsch_scheduler.schedule_slot_frame_size
            packedData, serial_pkt = common.tsch_build_pkt(
                payload, current_sf_size, self.increase_cycle_sequence())
            # Send NC packet
            self.reliable_send(
                packedData, serial_pkt.reserved0+1)

    """ Routing related functions """
    @property
    def router(self):
        return self.__router

    def send_routes(self):
        logger.info('Sending routes')
        num_pkts = 0
        payload = []
        for _, row in self.router.routing_table_routes.iterrows():
            scr = row['scr']
            dst = row['dst']
            via = row['via']
            data = {"scr": scr, "dst": dst, "via": via}
            logger.debug("route")
            logger.debug(data)
            route_pkt = RA_Packet_Payload(
                dst=dst, scr=scr, via=via, payload=payload)
            routed_packed = route_pkt.pack()
            payload = routed_packed
            if len(payload) > 90:
                logger.debug(f'Sending routing packet {num_pkts}')
                # We send the current payload
                num_pkts += 1
                packedData, serial_pkt = common.routing_build_pkt(
                    payload, self.increase_cycle_sequence())
                payload = []
                # Send NC packet
                self.reliable_send(
                    packedData, serial_pkt.reserved0+1)
        # Send the remain payload if there is one
        if payload:
            num_pkts += 1
            logger.debug(f'Sending routing packet {num_pkts}')
            packedData, serial_pkt = common.routing_build_pkt(
                payload, self.increase_cycle_sequence())
            # Send NC packet
            self.reliable_send(
                packedData, serial_pkt.reserved0+1)

    def compute_routes(self, G):
        return self.router.run(G)

    """ Reinforcement learning functionalities """

    def get_state(self):
        # Let's return the user requirements, last tsch schedule, current slotframe size
        alpha, beta, delta = self.user_requirements
        return alpha, beta, delta, self.last_tsch_link, self.current_slotframe_size

    def save_observations(self, **env_kwargs):
        self.db.save_observations(**env_kwargs)
        self.update_observations(**env_kwargs)

    def calculate_reward(self, alpha, beta, delta, slotframe_size):
        return self.__reward_processing.calculate_reward(alpha, beta, delta, self.cycle_sequence)

    """ User requirements functions """
    @property
    def user_requirements(self):
        return self.__alpha, self.__beta, self.__delta

    @user_requirements.setter
    def user_requirements(self, val):
        try:
            alpha, beta, delta = val
        except ValueError:
            raise ValueError("Pass an iterable with three items")
        else:
            """ This will run only if no exception was raised """
            self.__alpha = alpha
            self.__beta = beta
            self.__delta = delta

    @property
    def last_tsch_link(self):
        self.__last_tsch_link = self.last_active_tsch_slot()
        return self.__last_tsch_link

    @last_tsch_link.setter
    def last_tsch_link(self, val):
        # We pass because this is not valid in TSCH network
        # Automatically done by the scheduler
        pass

    @property
    def current_slotframe_size(self):
        return self.__current_slotframe_size

    @current_slotframe_size.setter
    def current_slotframe_size(self, val):
        self.__current_slotframe_size = val
