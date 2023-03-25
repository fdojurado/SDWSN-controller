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
from rich.table import Table

import logging

import networkx as nx

import numpy as np

import pandas as pd

from rich.progress import Progress

from sdwsn_controller.common import common
from sdwsn_controller.node.node import Node
from sdwsn_controller.packet.packet import Cell_Packet_Payload
from sdwsn_controller.packet.packet import RA_Packet_Payload
from sdwsn_controller.packet.packet_dissector import PacketDissector

from time import sleep

import threading

logger = logging.getLogger(f'main.{__name__}')


class Network():
    def __init__(
        self,
        config,
        socket
    ) -> None:
        processing_window = config.network.processing_window
        tsch_max_ch = config.tsch.max_channel
        tsch_max_sf = config.tsch.max_slotframe
        self.nodes = {}
        self.max_node_id = 0
        self.socket = socket
        self.packet_dissector = PacketDissector(
            network=self,
            config=config
        )
        self.network_running = False
        self.processing_window = processing_window
        self.read_socket_thread = None
        self.tsch_slotframe_size = 0
        self.tsch_max_ch = tsch_max_ch
        self.tsch_max_sf = tsch_max_sf
        self.name = "Cooja network"
        self.__timeout = 1.2
        # Callbacks
        self.energy_callback = None
        self.delay_callback = None
        self.pdr_callback = None
        self.reset_stats()

    def reset_stats(self):
        self.stats_tsch_pkt_sent = 0
        self.stats_routing_pkt_sent = 0
        self.stats_na_rcv = 0
        self.stats_data_rcv = 0

    # ---------------------------------------------------------------------------

    def nodes_clear(self):
        self.nodes = {}

    def nodes_size(self):
        return len(self.nodes)

    def nodes_get(self, id):
        return self.nodes.get(id)

    def nodes_add(self, id, sid=None, cycle_seq=None, rank=None):
        node = self.nodes_get(id)
        if node is not None:
            logger.debug(f"Node ID {id} already exists.")
            if rank is not None:
                node.rank = rank
            if cycle_seq is not None:
                node.cycle_seq = cycle_seq
            return node
        node = Node(id, sid=sid, rank=rank, cycle_seq=cycle_seq)
        if self.energy_callback:
            node.energy_register_callback(callback=self.energy_callback)
        if self.delay_callback:
            node.delay_register_callback(callback=self.delay_callback)
        if self.pdr_callback:
            node.pdr_register_callback(callback=self.pdr_callback)
        self.nodes.update({id: node})
        if id > self.max_node_id:
            self.max_node_id = id
        return node

    def nodes_print(self):
        for node in self.nodes.values():
            node.neighbor_print()
            node.tsch_print()
            node.route_print()
            node.energy_print()
            node.delay_print()
            node.pdr_print()

    def nodes_last_rank(self) -> int:
        last_rank = 0
        for node in self.nodes.values():
            if node.rank > last_rank:
                last_rank = node.rank
        return last_rank

    def nodes_performance_metrics_clear(self):
        for node in self.nodes.values():
            node.performance_metrics_clear()

    # ---------------------------------------------------------------------------

    def routes_clear(self):
        for node in self.nodes.values():
            node.route_clear()

    def routes_print(self):
        table = Table(title="Network routing table")

        table.add_column("Source", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Destination", justify="center", style="magenta")
        table.add_column("Via", justify="left", style="green")
        for node in self.nodes.values():
            for route in node.routes_get().values():
                dst_id = self.nodes_get(route.dst_id).sid
                nxt_hop = self.nodes_get(route.nexthop_id).sid
                table.add_row(node.sid, dst_id, nxt_hop)

        logger.debug(f"Network routing table\n{common.log_table(table)}")

    def routes_get(self):
        routes = {}
        for node in self.nodes.values():
            routes.update({node: node.routes_get()})
        return routes

    def routes_sendall(self):
        logger.debug('Sending all routes')
        sent = 0
        num_pkts = 0
        payload = []
        for node, routes in self.routes_get().items():
            for route in routes.values():
                scr = node.sid
                dst = self.nodes_get(route.dst_id).sid
                via = self.nodes_get(route.nexthop_id).sid
                route_pkt = RA_Packet_Payload(
                    dst=dst, scr=scr, via=via, payload=payload)
                routed_packed = route_pkt.pack()
                payload = routed_packed
                if len(payload) > 80:
                    num_pkts += 1
                    logger.debug(
                        f'Sending routing packet {num_pkts} with \
                            {len(payload)} bytes')
                    # We send the current payload
                    packedData, serial_pkt = common.routing_build_pkt(
                        payload, self.cycle_sequence_increase())
                    payload = []
                    # Send NC packet
                    if self.reliable_send(
                            packedData, serial_pkt.reserved0+1):
                        sent += 1
        # Send the remain payload if there is one
        if payload:
            num_pkts += 1
            logger.debug(
                f'Sending routing packet {num_pkts} with {len(payload)} bytes')
            packedData, serial_pkt = common.routing_build_pkt(
                payload, self.cycle_sequence_increase())
            # Send NC packet
            if self.reliable_send(
                    packedData, serial_pkt.reserved0+1):
                sent += 1
        # Update stats
        self.stats_routing_pkt_sent += num_pkts
        if sent == num_pkts:
            return 1
        else:
            return 0

    # ---------------------------------------------------------------------------
    def cycle_sequence(self):
        return self.packet_dissector.cycle_sequence

    def cycle_sequence_increase(self):
        cycle_seq = self.cycle_sequence()+1
        self.packet_dissector.cycle_sequence = cycle_seq
        # Clear the sequence
        self.packet_dissector.sequence = 0
        self.nodes_performance_metrics_clear()
        return self.packet_dissector.cycle_sequence
    # ---------------------------------------------------------------------------

    def tsch_link_exists(self, tx, rx) -> bool:
        return tx.tsch_link_exists(rx.id)

    def tsch_timeslot_free(self, ts) -> bool:
        ts_free = True
        for node in self.nodes.values():
            if not node.tsch_timeslot_free(ts):
                ts_free = False
                break
        return ts_free

    def tsch_last_ts(self) -> int:
        """
        Last active TSCH timeslot

        Returns:
            int: Last active timeslot in the current schedule.
        """
        last_ts = 0
        for node in self.nodes.values():
            if node.tsch_last_ts() > last_ts:
                last_ts = node.tsch_last_ts()
        return last_ts

    def tsch_last_ch(self):
        last_ch = 0
        for node in self.nodes.values():
            if node.tsch_last_ch() > last_ch:
                last_ch = node.tsch_last_ch()
        return last_ch

    def tsch_print(self):
        # Get the last active timeslot and channel
        max_columns = self.tsch_last_ts()
        max_rows = self.tsch_last_ch()
        # Create a pandas dataframe
        df = pd.DataFrame(index=range(0, max_rows+1),
                          columns=range(0, max_columns+1))

        for node in self.nodes.values():
            for sch in node.tsch_get().values():
                if sch.schedule_type == 1:  # Tx?
                    df.iloc[sch.ch,
                            sch.ts] = f"({node.sid}-{self.nodes_get(sch.dst_id).sid})"

        df.fillna('-', inplace=True)

        table = Table(
            title=f"TSCH network schedules (Row -> Channels, Columns -> \
                Timeoffsets) - Current SF size: {self.tsch_slotframe_size}",
            show_lines=True)

        show_index = True

        index_name = ''

        if show_index:
            index_name = str(index_name) if index_name else ""
            table.add_column(index_name)

        for column in df.columns:
            table.add_column(str(column), justify="center")

        for index, value_list in enumerate(df.values.tolist()):
            row = [str(index)] if show_index else []
            row += [str(x) for x in value_list]
            table.add_row(*row)

        logger.debug(f"TSCH schedules table grid\n{common.log_table(table)}")

    def tsch_clear(self):
        for node in self.nodes.values():
            node.tsch_clear()

    def tsch_schedules(self):
        routes = {}
        for node in self.nodes.values():
            routes.update({node.id: node.tsch_get()})
        return routes

    def tsch_sendall(self):
        logger.debug(f"Sending all schedules (SF: {self.tsch_slotframe_size})")
        sent = 0
        num_pkts = 0
        payload = []
        for node, schedules in self.tsch_schedules().items():
            for schedule in schedules.values():
                ch = schedule.ch
                ts = schedule.ts
                dst = schedule.dst_id
                schedule_type = schedule.schedule_type
                cell_pkt = Cell_Packet_Payload(payload=payload, type=schedule_type,
                                               channel=ch, timeslot=ts, scr=node,
                                               dst=dst)
                cell_packed = cell_pkt.pack()
                payload = cell_packed
                if len(payload) > 80:
                    num_pkts += 1
                    logger.debug(
                        f'Sending TSCH packet {num_pkts} with {len(payload)} bytes')
                    # We send the current payload
                    current_sf_size = 0
                    if num_pkts == 1:
                        current_sf_size = self.tsch_slotframe_size
                    packedData, serial_pkt = common.tsch_build_pkt(
                        payload, current_sf_size, self.cycle_sequence_increase())
                    payload = []
                    # Send NC packet
                    if self.reliable_send(
                            packedData, serial_pkt.reserved0+1):
                        sent += 1
        # Send the remain payload if there is one
        if payload:
            num_pkts += 1
            logger.debug(
                f'Sending TSCH packet {num_pkts} with {len(payload)} bytes')
            current_sf_size = 0
            if num_pkts == 1:
                current_sf_size = self.tsch_slotframe_size
            packedData, serial_pkt = common.tsch_build_pkt(
                payload, current_sf_size, self.cycle_sequence_increase())
            # Send NC packet
            if self.reliable_send(
                    packedData, serial_pkt.reserved0+1):
                sent += 1
        # Update stats
        self.stats_tsch_pkt_sent += num_pkts
        if sent == num_pkts:
            return 1
        else:
            return 0

    # --------------------------------------------------------------------

    def links(self):
        # Get last index of sensor
        N = self.max_node_id+1
        # Neighbor matrix
        nbr_rssi_matrix = np.zeros(shape=(N, N))
        # We first loop through all sensor nodes
        for node in self.nodes.values():
            nbrs = node.neighbors_get().values()
            for nbr in nbrs:
                scr = node.id
                dst = nbr.neighbor_id
                rssi = nbr.rssi
                nbr_rssi_matrix[int(scr)][int(
                    dst)] = int(rssi)
        matrix = nbr_rssi_matrix * -1
        G = nx.from_numpy_array(matrix, create_using=nx.DiGraph)
        G.remove_nodes_from(list(nx.isolates(G)))
        return G

    def wait(self) -> bool:
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
                    progress.update(
                        task1, completed=self.packet_dissector.sequence)
                    if self.packet_dissector.sequence >= self.processing_window:
                        result = 1
                        progress.update(task1, completed=100)
                    sleep(0.1)
            logger.info(f"cycle finished, result: {result}")
            return result
        else:
            return True

    # ---------------------Socket send related functions-------------------

    @property
    def timeout(self):
        return self.__timeout

    @timeout.setter
    def timeout(self, val):
        self.__timeout = val

    def send(self, data):
        if self.socket is not None:
            if self.network_running:
                # Send data to the serial send interface
                self.socket.send(data)
            else:
                logger.warning("Couldn't send data, network is Not running")

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
                    if (rtx >= 7):
                        logger.warning("ACK never received")
                        break
                    # We resend the packet if retransmission < 7
                    rtx = rtx + 1
                    self.send(data)
                sleep(self.timeout)
            return result

    # --------------------------socket primitives-----------------------

    def socket_read(self):
        if self.socket is not None:
            while (1):
                try:
                    msg = self.socket.recv(0.1)
                    if (len(msg) > 0):
                        self.packet_dissector.handle_serial_packet(msg)
                except TypeError:
                    pass
                if not self.network_running:
                    break
            logger.debug("Socket reading thread exited.")

    def socket_start(self) -> bool:
        if self.socket is not None:
            # Connect serial
            if self.socket.connect() != 0:
                logger.warning(
                    f'unsuccessful serial connection (host:{self.socket.host}, port: {self.socket.port})')
                return False
            logger.info("Socket up and running")
            # Read serial
            self.read_socket_thread = threading.Thread(
                target=self.socket_read)
            self.read_socket_thread.start()
            return True

    def socket_stop(self):
        if self.socket is not None:
            logger.debug(
                f"Shutting down socket {self.network_running}")
            if self.read_socket_thread is not None:
                self.read_socket_thread.join()
            self.socket.shutdown()

    # --------------------------------Callbacks-----------------------------
    def register_energy_callback(self, callback):
        # Register callback to every node in the network
        for node in self.nodes.values():
            node.energy_register_callback(callback)
        self.energy_callback = callback

    def register_delay_callback(self, callback):
        # Register callback to every node in the network
        for node in self.nodes.values():
            node.delay_register_callback(callback)
        self.delay_callback = callback

    def register_pdr_callback(self, callback):
        # Register callback to every node in the network
        for node in self.nodes.values():
            node.pdr_register_callback(callback)
        self.pdr_callback = callback
    # --------------------------Controller primitives-----------------------

    def stop(self):
        # Clear the running flag
        self.network_running = False
        self.nodes_clear()
        # Stop the socket
        self.socket_stop()

    def start(self):
        # Start the socket interface
        sock = self.socket_start()
        if not sock:
            self.stop()
            return
        self.network_running = True
