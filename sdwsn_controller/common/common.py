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

""" This python script holds common functions used across the controller """
import numpy as np
from sdwsn_controller.packet.packet import Cell_Packet, SDN_IP_Packet, SerialPacket, RA_Packet
from sdwsn_controller.packet.packet import sdn_protocols, SDN_SAH_LEN, SDN_IPH_LEN, SDN_RAH_LEN
from random import randrange
from rich.console import Console
from rich.text import Text
import logging

logger = logging.getLogger(f'main.{__name__}')


def log_table(rich_table):
    """Generate an ascii formatted presentation of a Rich table
    Eliminates any column styling
    """
    console = Console(width=150)
    with console.capture() as capture:
        console.print(rich_table)
    return Text.from_ansi(capture.get())


""" Build SA control packet """


def tsch_build_pkt(payloadPacked, sf_len, seq):
    logger.debug(f'Building TSCH packet with SF len {sf_len} and seq {seq}')
    payload_len = len(payloadPacked)
    # Build schedule packet header
    cell_pkt = Cell_Packet(
        payloadPacked, payload_len=payload_len, sf_len=sf_len, seq=seq)
    # Pack
    cell_packed = cell_pkt.pack()
    logger.debug(repr(cell_pkt))
    # Build sdn IP packet
    # 0x24: version 2, protocol SA = 4
    vap = (0x01 << 5) | sdn_protocols.SDN_PROTO_SA
    # length of the entire packet
    length = payload_len+SDN_SAH_LEN+SDN_IPH_LEN
    ttl = 0x32  # 0x40: Time to live
    scr = 0x0101  # Controller is sending
    dest = int(float(0))
    # Layer three layer packet
    sdn_ip_pkt = SDN_IP_Packet(cell_packed,
                               vap=vap, tlen=length, ttl=ttl, scr=scr, dest=dest)
    # Pack layer three packet
    sdn_ip_packed = sdn_ip_pkt.pack()
    logger.debug(repr(sdn_ip_pkt))
    # Build serial packet
    serial_pkt = SerialPacket(sdn_ip_packed, addr=0, pkt_chksum=0,
                              message_type=2, payload_len=length,
                              reserved0=randrange(1, 254), reserved1=0)
    packedData = serial_pkt.pack()
    logger.debug(repr(serial_pkt))
    return packedData, serial_pkt


""" Build RA control packet """


def routing_build_pkt(payloadPacked, seq):
    logger.debug(f'Building routes packet with seq {seq}')
    payload_len = len(payloadPacked)
    # Build RA packet
    ra_pkt = RA_Packet(
        payloadPacked, payload_len=payload_len, seq=seq)
    ra_packed = ra_pkt.pack()
    logger.debug(repr(ra_pkt))
    logger.debug(ra_packed)
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
    serial_pkt = SerialPacket(sdn_ip_packed, addr=0, pkt_chksum=0,
                              message_type=2, payload_len=length,
                              reserved0=randrange(1, 254), reserved1=0)
    packedData = serial_pkt.pack()
    return packedData, serial_pkt


def build_link_schedules_matrix_obs(packet_dissector, mySchedule):
    logger.info("building link schedules matrix")
    # Get last index of sensor
    N = packet_dissector.get_last_index_wsn()+1
    # This is an array of schedule matrices
    link_schedules_matrix = [None] * N
    # Last timeslot offset of the current schedule
    last_ts = 0
    # We now loop through the entire array and fill it with the schedule information
    for node in mySchedule.list_nodes:
        # Construct the schedule matrix
        schedule = np.zeros(
            shape=(mySchedule.num_channel_offsets, mySchedule.slotframe_size))
        for rx_cell in node.rx:
            # logger.info("node is listening in ts " +
            #       str(rx_cell.timeoffset)+" ch "+str(rx_cell.channeloffset))
            schedule[rx_cell.channeloffset][rx_cell.timeoffset] = 1
            if rx_cell.timeoffset > last_ts:
                last_ts = rx_cell.timeoffset
        for tx_cell in node.tx:
            # logger.info("node is transmitting in ts " +
            #       str(tx_cell.timeoffset)+" ch "+str(tx_cell.channeloffset))
            schedule[tx_cell.channeloffset][tx_cell.timeoffset] = -1
            if tx_cell.timeoffset > last_ts:
                last_ts = tx_cell.timeoffset
        addr = node.node.split(".")
        link_schedules_matrix[int(
            addr[0])] = schedule.flatten().tolist()
    # logger.info("link_schedules_matrix")
    # logger.info(link_schedules_matrix)
    # using list comprehension
    # to remove None values in list
    res = [i for i in link_schedules_matrix if i]
    # Save in DB
    # current_time = datetime.now().timestamp() * 1000.0
    # data = {
    #     "timestamp": current_time,
    #     "schedules": res
    # }
    # Database.insert(SCHEDULES, data)
    return res, last_ts


""" Coprime checks methods """

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27


def gcd(p, q):
    # Create the gcd of two positive integers.
    while q != 0:
        p, q = q, p % q
    return p


def fc_is_coprime(x, y):
    return gcd(x, y) == 1


def compare_coprime(num):
    sf_sizes = [eb_size, common_size, control_plane_size]
    result = 0
    for sf_size in sf_sizes:
        is_coprime = fc_is_coprime(num, sf_size)
        result += is_coprime

    if result == 3:
        return 1
    else:
        return 0


def next_coprime(num):
    is_coprime = 0
    while not is_coprime:
        num += 1
        # Check if num is coprime with all other sf sizes
        is_coprime = compare_coprime(num)
    return num


def previous_coprime(num):
    is_coprime = 0
    while not is_coprime:
        num -= 1
        # Check if num is coprime with all other sf sizes
        is_coprime = compare_coprime(num)
    return num
