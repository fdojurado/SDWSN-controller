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

from sdwsn_controller.packet.packet import Cell_Packet_Payload
from sdwsn_controller.packet.packet import RA_Packet_Payload
from sdwsn_controller.database.database import OBSERVATIONS
from sdwsn_controller.database.database import NODES_INFO
from sdwsn_controller.common import common
from abc import ABC, abstractmethod
from rich.progress import Progress
from time import sleep
import numpy as np
import networkx as nx

import threading
import logging

logger = logging.getLogger('main.'+__name__)


class BaseController(ABC):
    """
    The BaseController class is an abstract class. Some functionalities are declared
    as abstract methods, classes that inherits from the BaseController should take care
    of them. The controller has four main modules: router, tsch scheduler, packet dissector,
    and communication interface.
    """

    def __init__(
        self,
        # Sink/socket communication
        socket: object = None,
        # Database
        db: object = None,
        # RL related
        reward_processing: object = None,
        # Packet dissector
        packet_dissector: object = None,
        # Window
        processing_window: int = 200,
        # Routing
        router: object = None,
        # TSCH scheduler
        tsch_scheduler: object = None
    ):
        # Database
        self.__db = db
        if self.__db is not None:
            logger.info(f'Database added')

        # Create reward module; only for RL
        self.__reward_processing = reward_processing
        if reward_processing is not None:
            self.__reward_processing = reward_processing
            logger.info(f"reward processing: {self.reward_processing.name}")
            # Requirements
            self.__user_requirements = UserRequirements()

        # Create packet dissector
        self.__packet_dissector = packet_dissector
        if packet_dissector is not None:
            logger.info(f'Packet dissector: {self.packet_dissector.name}')

        # Create TSCH scheduler module
        self.__tsch_scheduler = tsch_scheduler
        if router is not None:
            logger.info(f'TSCH scheduler: {self.tsch_scheduler.name}')

        # Create an instance of Router
        self.__router = router
        if router is not None:
            logger.info(f'Routing: {self.router.name}')

        # We only create the socket module if this is explicitly pass to the class.
        # This is is because numerical env does not use it.
        self.__socket = socket
        if socket is not None:
            logger.info(f'Socket added')

        # Processing window
        self.__processing_window = processing_window
        logger.info(f'Processing window: {self.__processing_window}')

        self.__is_running = False
        self.__read_socket_thread = None

        super().__init__()
   # ---------------------Database functionalities---------------------------

    def init_db(self):
        if self.db is not None:
            logger.info("Initializing DB")
            self.db.initialize()

    @property
    def db(self):
        return self.__db

    # -------------------Packet dissector functionalities--------------------

    @property
    def sequence(self):
        if self.packet_dissector is not None:
            return self.packet_dissector.sequence

    @sequence.setter
    def sequence(self, num):
        if self.packet_dissector is not None:
            self.packet_dissector.sequence = num

    @property
    def cycle_sequence(self):
        if self.packet_dissector is not None:
            return self.packet_dissector.cycle_sequence

    @cycle_sequence.setter
    def cycle_sequence(self, num):
        if self.packet_dissector is not None:
            self.packet_dissector.cycle_sequence = num

    def increase_cycle_sequence(self):
        if self.packet_dissector is not None:
            self.cycle_sequence += 1
            return self.cycle_sequence

    def reset_pkt_sequence(self):
        if self.packet_dissector is not None:
            self.packet_dissector.sequence = 0

    # Packet dissector
    @property
    def packet_dissector(self):
        return self.__packet_dissector

    # --------------------------TSCH functions--------------------------

    def send_tsch_schedules(self):
        if self.tsch_scheduler is not None:
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

    def compute_tsch_schedule(self, path, current_sf_size):
        if self.tsch_scheduler is not None:
            # We clean previous schedule first
            self.tsch_scheduler.schedule_clear_schedule()
            self.tsch_scheduler.run(path, current_sf_size)

    @property
    def last_tsch_link(self):
        if self.tsch_scheduler is not None:
            return self.tsch_scheduler.schedule_last_active_ts()

    @last_tsch_link.setter
    def last_tsch_link(self, val):
        # We pass because this is not valid in TSCH network
        # Automatically done by the scheduler
        pass

    @property
    def current_slotframe_size(self):
        if self.tsch_scheduler is not None:
            return self.tsch_scheduler.schedule_slot_frame_size

    @current_slotframe_size.setter
    def current_slotframe_size(self, val):
        if self.tsch_scheduler is not None:
            self.tsch_scheduler.schedule_slot_frame_size = val

    @property
    def tsch_scheduler(self):
        return self.__tsch_scheduler

    # --------------------------Routing functions-------------------------

    def send_routes(self):
        if self.router is not None:
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
        if self.router is not None:
            return self.router.run(G)

    def get_network_links(self):
        if self.router is not None:
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

    @property
    def router(self):
        return self.__router

    # --------------------------Sink interface----------------------------

    @property
    def read_socket_thread(self):
        if self.socket is not None:
            return self.__read_socket_thread

    @read_socket_thread.setter
    def read_socket_thread(self, val):
        if self.socket is not None:
            self.__read_socket_thread = val

    def comm_interface_start(self):
        if self.socket is not None:
            # Connect serial
            if self.socket.connect() != 0:
                logger.warning(
                    f'unsuccessful serial connection (host:{self.socket.host}, port: {self.socket.port})')
                return 0
            logger.info("Socket up and running")
            # Read serial
            self.read_socket_thread = threading.Thread(
                target=self.comm_interface_read)
            self.read_socket_thread.start()
            return 1

    def comm_interface_stop(self):
        if self.socket is not None:
            logger.info(
                f"start to shutdown thread, running flag = {self.controller_running}")
            if self.read_socket_thread is not None:
                self.read_socket_thread.join()
            self.socket.shutdown()

    def comm_interface_read(self):
        if self.socket is not None:
            while(1):
                try:
                    msg = self.socket.recv(0.1)
                    if(len(msg) > 0):
                        self.packet_dissector.handle_serial_packet(msg)
                except TypeError:
                    pass
                if not self.controller_running:
                    break
            logger.info("Socket reading thread exited.")

    @property
    def socket(self):
        return self.__socket

    # --------------------------Controller primitives-----------------------

    @property
    def processing_window(self):
        return self.__processing_window

    @processing_window.setter
    def processing_window(self, val):
        self.__processing_window = val

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
        self.controller_running = True
        # self.controller_start()

    @property
    def controller_running(self):
        return self.__is_running

    @controller_running.setter
    def controller_running(self, val):
        self.__is_running = val

    def stop(self):
        # Clear the running flag
        self.controller_running = False
        # Stop the serial interface
        self.comm_interface_stop()
        # Reset the packet dissector sequence
        self.cycle_sequence = 0
        self.sequence = 0

    @abstractmethod
    def reset(self):
        pass

    def wait(self):
        """
         We wait for the current cycle to finish
         """
        # If we have not received any data after looping 10 times
        # We return
        if self.processing_window is not None:
            logger.info(
                "Starting new cycle")
            result = -1

            with Progress(transient=True) as progress:
                task1 = progress.add_task(
                    "[red]Waiting for the current cycle to finish...", total=self.processing_window)

                while not progress.finished:
                    progress.update(task1, completed=self.sequence)
                    if self.sequence >= self.processing_window:
                        result = 1
                        logger.info(f"Cycle completed")
                        progress.update(task1, completed=100)
                    sleep(0.1)
            logger.info(f"cycle finished, result: {result}")
            return result
        else:
            return True

    @abstractmethod
    def timeout(self):
        pass

    def processing_wait(self, time):
        sleep(time)

    def wait_seconds(self, seconds):
        sleep(seconds)

    def send(self, data):
        if self.socket is not None:
            if self.controller_running:
                # Send data to the serial send interface
                self.socket.send(data)
            else:
                logger.warning("Couldn't send data, controller is Not running")

    def reliable_send(self, data, ack):
        if self.packet_dissector is not None:
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
                self.timeout()
            return result

    # --------------------------Reinforcement Learning----------------------

    @property
    def reward_processing(self):
        return self.__reward_processing

    def export_observations(self, simulation_name, folder):
        if self.db is not None:
            self.db.export_collection(OBSERVATIONS, simulation_name, folder)

    def calculate_reward(self, alpha, beta, delta, _):
        if self.reward_processing is not None:
            return self.reward_processing.calculate_reward(alpha, beta, delta, self.cycle_sequence)

    @property
    def user_requirements(self):
        return self.__user_requirements.requirements

    @user_requirements.setter
    def user_requirements(self, val):
        self.__user_requirements.requirements = val

    @property
    def alpha(self):
        return self.__user_requirements.alpha

    @alpha.setter
    def alpha(self, val):
        self.__user_requirements.alpha = val

    @property
    def beta(self):
        return self.__user_requirements.beta

    @beta.setter
    def beta(self, val):
        self.__user_requirements.beta = val

    @property
    def delta(self):
        return self.__user_requirements.delta

    @delta.setter
    def delta(self, val):
        self.__user_requirements.delta = val

    def save_observations(self, **env_kwargs):
        if self.db is not None:
            self.db.save_observations(**env_kwargs)

        self.__update_observations(**env_kwargs)

    def __update_observations(self, timestamp, alpha, beta, delta, power_wam, power_mean,
                              power_normalized, delay_wam, delay_mean, delay_normalized,
                              pdr_wam, pdr_mean, current_sf_len, last_ts_in_schedule, reward):
        self.__timestamp = timestamp
        self.alpha = alpha
        self.beta = beta
        self.delta = delta
        self.__power_wam = power_wam
        self.__power_mean = power_mean
        self.__power_normalized = power_normalized
        self.__delay_wam = delay_wam
        self.__delay_mean = delay_mean
        self.__delay_normalized = delay_normalized
        self.__pdr_wam = pdr_wam
        self.__pdr_mean = pdr_mean
        self.__current_slotframe_size = current_sf_len
        self.__last_tsch_link = last_ts_in_schedule
        self.__reward = reward

    def delete_info_collection(self):
        if self.db is not None:
            self.db.delete_collection(NODES_INFO)

    def get_state(self):
        # Let's return the user requirements, last tsch schedule, current slotframe size
        state = {
            "user_requirements": self.user_requirements,
            "alpha": self.alpha,
            "beta": self.beta,
            "delta": self.delta,
            "last_ts_in_schedule": self.__last_tsch_link,
            "current_sf_len": self.__current_slotframe_size
        }
        return state

# User requirements class; this is only for RL


class UserRequirements():
    def __init__(self):
        pass

    @property
    def requirements(self):
        user_req = [
            self.alpha,
            self.beta,
            self.delta
        ]
        return np.array(user_req)

    @requirements.setter
    def requirements(self, val):
        try:
            alpha, beta, delta = val
        except ValueError:
            raise ValueError("Pass an iterable with three items")
        else:
            """ This will run only if no exception was raised """
            self.alpha = alpha
            self.beta = beta
            self.delta = delta

    def check_valid_number(func):
        def inner(self, val):
            if val > 1 or val < 0:
                logger.error("Invalid user requirement value.")
                return

            return func(self, val)
        return inner

    @property
    def alpha(self):
        return self.__alpha

    @alpha.setter
    @check_valid_number
    def alpha(self, val):
        self.__alpha = val

    @property
    def beta(self):
        return self.__beta

    @beta.setter
    @check_valid_number
    def beta(self, val):
        self.__beta = val

    @property
    def delta(self):
        return self.__delta

    @delta.setter
    @check_valid_number
    def delta(self, val):
        self.__delta = val
