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
from typing import Dict, Optional, List, Any, Callable

import time
import logging
import threading
import numpy as np
import pandas as pd
import networkx as nx
from rich.table import Table
from rich.progress import Progress

from sdwsn_controller.common import common
from sdwsn_controller.node.node import Node
from sdwsn_controller.packet.packet import Cell_Packet_Payload, RA_Packet_Payload
from sdwsn_controller.packet.packet_dissector import PacketDissector


logger = logging.getLogger(f'main.{__name__}')


class Network:
    def __init__(
        self,
        config: Any,
        socket: Any
    ) -> None:
        processing_window = config.network.processing_window
        tsch_max_ch = config.tsch.max_channel
        tsch_max_sf = config.tsch.max_slotframe
        self.nodes: Dict[int, Node] = {}
        self.max_node_id: int = 0
        self.socket: Any = socket
        self.packet_dissector: PacketDissector = PacketDissector(
            network=self,
            config=config
        )
        self.network_running: bool = False
        self.processing_window: int = processing_window
        self.read_socket_thread: Optional[threading.Thread] = None
        self.tsch_slotframe_size: int = 0
        self.tsch_max_ch: int = tsch_max_ch
        self.tsch_max_sf: int = tsch_max_sf
        self.name: str = "Cooja network"
        self.__timeout: float = 1.2
        self.energy_callback: Optional[Callable] = None
        self.delay_callback: Optional[Callable] = None
        self.pdr_callback: Optional[Callable] = None
        self.reset_stats()

    def reset_stats(self) -> None:
        self.stats_tsch_pkt_sent: int = 0
        self.stats_routing_pkt_sent: int = 0
        self.stats_na_rcv: int = 0
        self.stats_data_rcv: int = 0

    def nodes_clear(self) -> None:
        self.nodes = {}

    def nodes_size(self) -> int:
        return len(self.nodes)

    def nodes_get(self, id: int) -> Optional[Node]:
        return self.nodes.get(id)

    def nodes_add(
        self,
        id: int,
        sid: Optional[int] = None,
        cycle_seq: Optional[int] = None,
        rank: Optional[int] = None
    ) -> Node:
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
        self.nodes[id] = node
        if id > self.max_node_id:
            self.max_node_id = id
        return node

    def nodes_print(self) -> None:
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

    def nodes_performance_metrics_clear(self) -> None:
        for node in self.nodes.values():
            node.performance_metrics_clear()

    # ---------------------------------------------------------------------------

    def routes_clear(self) -> None:
        for node in self.nodes.values():
            node.route_clear()

    def routes_print(self) -> None:
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

    def routes_get(self) -> dict:
        routes = {}
        for node in self.nodes.values():
            routes[node] = node.routes_get()
        return routes

    def routes_sendall(self):
        logger.debug('Sending all routes')
        sent = 0
        num_pkts = 0
        payload = None
        for node, routes in self.routes_get().items():
            for route in routes.values():
                src = node.sid
                dst = self.nodes_get(route.dst_id).sid
                via = self.nodes_get(route.nexthop_id).sid
                route_pkt = RA_Packet_Payload(
                    dst=dst, src=src, via=via, payload=payload)
                routed_pkt = route_pkt.pack()
                if len(routed_pkt) > 80:
                    num_pkts += 1
                    logger.debug(
                        f'Sending routing packet {num_pkts} with {len(routed_pkt)} bytes')
                    # We send the current payload
                    if self.send_routing_packet(routed_pkt):
                        sent += 1
                    payload = None
                else:
                    # Append the packet to the payload
                    payload = routed_pkt
        # Send the remaining payload if there is one
        if payload:
            num_pkts += 1
            logger.debug(
                f'Sending routing packet {num_pkts} with {len(payload)} bytes')
            if self.send_routing_packet(payload):
                sent += 1
        # Update stats
        self.stats_routing_pkt_sent += num_pkts
        return sent == num_pkts

    def send_routing_packet(self, payload):
        packed_data, serial_pkt = common.routing_build_pkt(
            payload, self.cycle_sequence_increase())
        # Send NC packet
        return self.reliable_send(packed_data, serial_pkt.reserved0+1)

    # ---------------------------------------------------------------------------
    def cycle_sequence(self) -> int:
        return self.packet_dissector.cycle_sequence

    def cycle_sequence_increase(self) -> int:
        cycle_seq = self.cycle_sequence() + 1
        self.packet_dissector.cycle_sequence = cycle_seq
        # Clear the sequence
        self.packet_dissector.sequence = 0
        self.nodes_performance_metrics_clear()
        return cycle_seq
    # ---------------------------------------------------------------------------

    def tsch_link_exists(self, tx, rx) -> bool:
        return tx.tsch_link_exists(rx.id)

    def tsch_timeslot_free(self, ts: int) -> bool:
        for node in self.nodes.values():
            if not node.tsch_timeslot_free(ts):
                return False
        return True

    def tsch_last_ts(self) -> int:
        last_ts = 0
        for node in self.nodes.values():
            last_ts = max(last_ts, node.tsch_last_ts())
        return last_ts

    def tsch_last_ch(self) -> int:
        last_ch = 0
        for node in self.nodes.values():
            last_ch = max(last_ch, node.tsch_last_ch())
        return last_ch

    def tsch_print(self):
        # Get the last active timeslot and channel
        max_columns = self.tsch_last_ts()
        max_rows = self.tsch_last_ch()
        # Create a pandas dataframe
        df = pd.DataFrame(index=range(max_rows+1),
                          columns=range(max_columns+1))

        for node in self.nodes.values():
            for sch in node.tsch_get().values():
                if sch.schedule_type == 1:  # Tx?
                    dst_id = sch.dst_id
                    dst = self.nodes_get(dst_id).sid
                    df.iloc[sch.ch, sch.ts] = f"({node.sid}-{dst})"

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
            row: List[str] = [str(index)] if show_index else []
            row += [str(x) for x in value_list]
            table.add_row(*row)

        logger.debug(f"TSCH schedules table grid\n{common.log_table(table)}")

    def tsch_clear(self):
        for node in self.nodes.values():
            node.tsch_clear()

    def tsch_schedules(self):
        routes = {}
        for node_id, schedules in self.nodes.items():
            routes[node_id] = schedules.tsch_get()
        return routes

    def tsch_sendall(self):
        logger.debug(f"Sending all schedules (SF: {self.tsch_slotframe_size})")
        sent = 0
        num_pkts = 0
        payload = None
        for node_id, schedules in self.tsch_schedules().items():
            for schedule in schedules.values():
                ch = schedule.ch
                ts = schedule.ts
                dst = schedule.dst_id
                schedule_type = schedule.schedule_type
                cell_pkt = Cell_Packet_Payload(payload=payload, type=schedule_type,
                                               channel=ch, timeslot=ts, scr=node_id,
                                               dst=dst)
                cell_packed = cell_pkt.pack()
                if len(cell_packed) > 80:
                    num_pkts += 1
                    logger.debug(
                        f'Sending TSCH packet {num_pkts} with {len(payload)} bytes')
                    # We send the current payload
                    current_sf_size = self.tsch_slotframe_size if num_pkts == 1 else 0
                    # We send the current payload
                    if self.send_tsch_packet(cell_packed, current_sf_size):
                        sent += 1
                    payload = None
                else:
                    payload = cell_packed
        # Send the remain payload if there is one
        if payload:
            num_pkts += 1
            logger.debug(
                f'Sending TSCH packet {num_pkts} with {len(payload)} bytes')
            current_sf_size = self.tsch_slotframe_size if num_pkts == 1 else 0
            if self.send_tsch_packet(payload, current_sf_size):
                sent += 1
        # Update stats
        self.stats_tsch_pkt_sent += num_pkts
        return sent == num_pkts

    def send_tsch_packet(self, payload, sf):
        packed_data, serial_pkt = common.tsch_build_pkt(
            payload, sf, self.cycle_sequence_increase())
        # Send NC packet
        return self.reliable_send(packed_data, serial_pkt.reserved0+1)

    # --------------------------------------------------------------------

    def links(self) -> nx.DiGraph:
        """
        Construct a directed graph of neighbor relationships based on RSSI values.
        """
        num_nodes = self.max_node_id + 1
        neighbor_matrix = np.zeros(shape=(num_nodes, num_nodes))
        for node in self.nodes.values():
            neighbors = node.neighbors_get().values()
            for nbr in neighbors:
                src = node.id
                dst = nbr.neighbor_id
                rssi = nbr.rssi
                neighbor_matrix[int(src)][int(dst)] = rssi
        matrix = neighbor_matrix * -1
        graph = nx.from_numpy_array(matrix, create_using=nx.DiGraph)
        graph.remove_nodes_from(list(nx.isolates(graph)))
        return graph

    def wait(self) -> bool:
        """Wait for the current cycle to finish."""
        if self.processing_window is not None:
            logger.info("Starting new cycle")
            result = -1

            with Progress(transient=True) as progress:
                task = progress.add_task(
                    "[red]Waiting for the current cycle to finish...", total=self.processing_window)

                while not progress.finished:
                    progress.update(
                        task, completed=self.packet_dissector.sequence)
                    if self.packet_dissector.sequence >= self.processing_window:
                        result = 1
                        progress.update(task, completed=100)
                    time.sleep(0.1)

            logger.info(f"Cycle finished, result: {result}")
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
                logger.warning("Couldn't send data, network is not running")

    def reliable_send(self, data, ack) -> bool:
        """
        Send data reliably to the serial interface.
        Retry sending up to `rtx_limit` times if no ACK is received.
        Return `True` if the ACK is received, `False` otherwise.
        """
        if not self.packet_dissector:
            # Packet dissector not available
            return False

        # Reliable socket data transmission
        rtx_limit = 7
        ack_received = False

        # Send packet and wait for ACK
        for rtx in range(rtx_limit):
            self.send(data)
            time.sleep(self.timeout)
            if self.packet_dissector.ack_pkt is not None:
                if self.packet_dissector.ack_pkt.reserved0 == ack:
                    logger.debug("Correct ACK received")
                    ack_received = True
                    break
                else:
                    logger.debug("Incorrect ACK received")
        else:
            # We reached the maximum number of retries without receiving an ACK
            logger.warning("Failed to send data reliably")

        return ack_received

    # --------------------------socket primitives-----------------------

    def read_socket(self):
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

    def start_socket(self) -> bool:
        if self.socket is not None:
            # Connect serial
            if self.socket.connect() != 0:
                logger.warning(
                    f'unsuccessful serial connection (host:{self.socket.host}, port: {self.socket.port})')
                return False
            logger.info("Socket up and running")
            # Read serial
            self.read_socket_thread = threading.Thread(
                target=self.read_socket)
            self.read_socket_thread.start()
            return True

    def stop_socket(self):
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
        self.stop_socket()

    def start(self):
        # Start the socket interface
        sock = self.start_socket()
        if not sock:
            self.stop()
            return
        self.network_running = True
