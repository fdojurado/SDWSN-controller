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

from logging import exception
# from src.sdwsn_forwarding_table.forwarding_table import FWD_TABLE
# from controller.routing.routing import *
# from src.sdwsn_network_reconfiguration.queue import Queue
from sdwsn_controller.packet.packet_dissector import *
from sdwsn_controller.packet.packet import SerialPacket, Cell_Packet, Cell_Packet_Payload, SDN_SAH_LEN, SDN_RAH_LEN, RA_Packet, RA_Packet_Payload
import networkx as nx
from time import sleep
import pandas as pd
import queue  # or Queue in Python 2
import types
# Generate random number for ack
from random import randrange
import json
from sdwsn_controller.controller import BaseController
from sdwsn_controller.serial.serial import SerialBus


""" TODO: Set the maximum routes per node (e.g., 10).
Remove old routes with the new ones"""


# job types for the NC
job_type = types.SimpleNamespace()
job_type.TSCH = 0
job_type.ROUTING = 1


class NetworkReconfig(BaseController):
    def __init__(
        self,
        serial_interface: type[SerialBus]
    ):
        super().__init__(
            serial_interface=serial_interface
        )

    def process_json_routes_packets(self, routes):
        # Let's loop into routes
        payload = []
        for rt in routes['routes']:
            route_pkt = RA_Packet_Payload(
                dst=rt['dst'], scr=rt['scr'], via=rt['via'], payload=payload)
            routed_packed = route_pkt.pack()
            payload = routed_packed
        return payload

    def build_routes_packet(self, data, routes_sequence):
        # print("building routing packet")
        # Build routes payload
        payloadPacked = self.process_json_routes_packets(data)
        # print("payload packed")
        # print(payloadPacked)
        payload_len = len(payloadPacked)
        # Build RA packet
        ra_pkt = RA_Packet(
            payloadPacked, payload_len=payload_len, seq=routes_sequence)
        ra_packed = ra_pkt.pack()
        # print(repr(ra_pkt))
        # print(ra_packed)
        # Build sdn IP packet
        # 0x23: version 2, protocol RA = 3
        vap = (0x01 << 5) | sdn_protocols.SDN_PROTO_RA
        # length of the entire packet
        length = payload_len+SDN_RAH_LEN+SDN_IPH_LEN
        ttl = 0x40  # 0x40: Time to live
        scr = 0x0101  # Controller is sending
        dest = int(float(0))
        sdn_ip_pkt = SDN_IP_Packet(ra_packed,
                                   vap=vap, tlen=length, ttl=ttl, scr=scr, dest=dest)
        sdn_ip_packed = sdn_ip_pkt.pack()
        # print(repr(sdn_ip_pkt))
        # Control packet as payload of the serial packet
        pkt = SerialPacket(sdn_ip_packed, addr=0, pkt_chksum=0,
                           message_type=2, payload_len=length,
                           reserved0=randrange(1, 254), reserved1=0)
        packedData = pkt.pack()
        # print(repr(pkt))
        return packedData, pkt

    def process_json_schedule_packets(self, schedules):
        # Let's loop into routes
        payload = []
        for cell in schedules['cells']:
            cell_pkt = Cell_Packet_Payload(type=int(cell['type']), channel=int(cell['channel']), timeslot=int(cell['timeslot']),
                                           scr=cell['addr'], dst=cell['dest'], payload=payload)
            cell_packed = cell_pkt.pack()
            payload = cell_packed
        return payload

    def build_schedule_packet(self, data, schedule_sequence):
        # print("building schedule packet")
        # Build schedules payload
        payloadPacked = self.process_json_schedule_packets(data)
        # print("payload packed")
        # print(payloadPacked)
        payload_len = len(payloadPacked)
        # Build schedule packet header
        cell_pkt = Cell_Packet(
            payloadPacked, payload_len=payload_len, sf_len=data['sf_len'], seq=schedule_sequence)
        cell_packed = cell_pkt.pack()
        # print(repr(rt_pkt))
        # print(cell_packed)
        # Build sdn IP packet
        # 0x24: version 2, protocol SA = 4
        vap = (0x01 << 5) | sdn_protocols.SDN_PROTO_SA
        # length of the entire packet
        length = payload_len+SDN_SAH_LEN+SDN_IPH_LEN
        ttl = 0x32  # 0x40: Time to live
        scr = 0x0101  # Controller is sending
        dest = int(float(0))
        sdn_ip_pkt = SDN_IP_Packet(cell_packed,
                                   vap=vap, tlen=length, ttl=ttl, scr=scr, dest=dest)
        sdn_ip_packed = sdn_ip_pkt.pack()
        # print(repr(sdn_ip_pkt))
        # Build serial packet
        pkt = SerialPacket(sdn_ip_packed, addr=0, pkt_chksum=0,
                           message_type=2, payload_len=length,
                           reserved0=randrange(1, 254), reserved1=0)
        packedData = pkt.pack()
        # print(repr(pkt))
        return packedData, pkt

    def send_nc(self, node, job_id):
        # look for incoming jobs
        data = json.loads(node)
        match(data['job_type']):
            case job_type.TSCH:
                print(f"TSCH job type (SEQ:{job_id})")
                packedData, serial_pkt = self.build_schedule_packet(
                    data, job_id)
            case job_type.ROUTING:
                print(f"Routing job type (SEQ:{job_id})")
                packedData, serial_pkt = self.build_routes_packet(
                    data, job_id)
            case _:
                print("unknown job type")
                return None
        # Send NC packet
        result = self.controller_reliable_send(
            packedData, serial_pkt.reserved0+1)
        # Send notification of job completion
        return result, job_id
