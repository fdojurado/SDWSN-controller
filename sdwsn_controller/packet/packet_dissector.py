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

# This class allows to read and write from the database
import logging

from sdwsn_controller.packet.packet import Data_Packet, NA_Packet, NA_Packet_Payload, SDN_NAPL_LEN
from sdwsn_controller.packet.packet import SerialPacket, SDN_IP_Packet
from sdwsn_controller.packet.packet import serial_protocol, sdn_protocols
from sdwsn_controller.packet.packet import SDN_IPH_LEN

import struct


logger = logging.getLogger(f'main.{__name__}')


class PacketDissector():
    def __init__(
            self,
            network,
            config
    ):
        self.ack_pkt = None
        self.cycle_sequence = 0
        self.sequence = 0
        self.network = network
        self.config = config

    def handle_serial_packet(self, data):
        # Let's parse serial packet
        serial_pkt = self.process_serial_packet(data)
        if serial_pkt is None:
            logger.warning("bad serial packet")
            return
        # Let's first save the packet
        # self.db.save_serial_packet(serial_pkt.toJSON())
        # Check if this is a serial ACK packet
        if serial_pkt.message_type == serial_protocol.ACK:
            self.ack_pkt = serial_pkt
            return
        # Let's now process the sdn IP packet
        pkt = self.process_sdn_ip_packet(serial_pkt.payload)
        # We exit processing if empty result returned
        if (not pkt):
            return
        b = int.from_bytes(b'\x0F', 'big')
        protocol = pkt.vap & b
        match protocol:
            case sdn_protocols.SDN_PROTO_NA:
                logger.debug("Processing NA packet")
                na_pkt = self.process_na_packet(pkt)
                if na_pkt is None:
                    logger.warning("bad NA packet")
                    return
                # Add to number of pkts received during this period
                if not na_pkt.cycle_seq == self.cycle_sequence:
                    return
                logger.debug(repr(pkt))
                logger.debug(repr(na_pkt))
                self.sequence += 1
                logger.debug(f"num seq (NA): {self.sequence}")
                node = self.network.nodes_add(
                    pkt.scr, cycle_seq=na_pkt.cycle_seq, rank=na_pkt.rank)
                node.energy_add(na_pkt.seq, na_pkt.energy)
                # Process neighbors
                blocks = len(na_pkt.payload) // SDN_NAPL_LEN
                idx_start = 0
                idx_end = 0
                for _ in range(1, blocks+1):
                    idx_end += SDN_NAPL_LEN
                    payload = na_pkt.payload[idx_start:idx_end]
                    idx_start = idx_end
                    payload_unpacked = NA_Packet_Payload.unpack(payload)
                    node.neighbor_add(payload_unpacked.addr, payload_unpacked.rssi,
                                      payload_unpacked.etx)
                return
            case sdn_protocols.SDN_PROTO_DATA:
                logger.debug("Processing data packet")
                data_pkt = self.process_data_packet(pkt)
                if data_pkt is None:
                    logger.warning("bad Data packet")
                    return
                # Add to number of pkts received during this period
                if not data_pkt.cycle_seq == self.cycle_sequence:
                    return
                logger.debug(repr(pkt))
                logger.debug(repr(data_pkt))
                self.sequence += 1
                logger.debug(f"num seq (data): {self.sequence}")
                node = self.network.nodes_add(
                    pkt.scr, cycle_seq=data_pkt.cycle_seq)
                # We now build the pdr DB
                node.pdr_add(data_pkt.seq)
                # We now build the delay DB
                sampled_delay = data_pkt.asn * self.config.tsch.slot_duration
                node.delay_add(data_pkt.seq, sampled_delay)
                return
            case _:
                logger.warning("sdn IP packet type not found")
                return

    def process_serial_packet(self, data):
        # Parse sdn IP packet
        logger.debug("processing serial packet")
        pkt = SerialPacket.unpack(data)
        logger.debug(repr(pkt))
        # If the reported payload length in the serial header doesn't match the packet size,
        # then we drop the packet.
        if (len(pkt.payload) < pkt.payload_len):
            logger.warning("packet shorter than reported in serial header")
            return None
        # serial packet succeed
        logger.debug("succeed unpacking serial packet")
        return pkt

    def process_data_packet(self, pkt):
        # If the reported length in the sdn IP header doesn't match the packet size,
        # then we drop the packet.
        if (len(pkt.payload) < (pkt.tlen-SDN_IPH_LEN)):
            logger.warning("Data packet shorter than reported in IP header")
            return
        # Process data packet header
        pkt = Data_Packet.unpack(pkt.payload)
        logger.debug(repr(pkt))
        # sdn IP packet succeed
        logger.debug("succeed unpacking sdn data packet")
        return pkt

    def process_sdn_ip_packet(self, data):
        # We first check the integrity of the HEADER of the sdn IP packet
        if (self.sdn_ip_checksum(data, SDN_IPH_LEN) != 0xffff):
            logger.warning("bad IP checksum")
            return
        # Parse sdn IP packet
        logger.debug("processing IP packet")
        pkt = SDN_IP_Packet.unpack(data)
        logger.debug(repr(pkt))
        # If the reported length in the sdn IP header doesn't match the packet size,
        # then we drop the packet.
        if (len(data) < pkt.tlen):
            logger.warning("packet shorter than reported in IP header")
            return
        # sdn IP packet succeed
        if pkt.dest == 257:  # 1.1 which is the controller
            self.network.nodes_add(id=0, sid="1.1", rank=0)
            self.network.nodes_add(id=1, rank=0)  # Also add sink
        logger.debug("succeed unpacking sdn IP packet")
        return pkt

    def chksum(self, sum, data, len):
        total = sum
        # Add up 16-bit words
        num_words = len // 2
        for chunk in struct.unpack("!%sH" % num_words, data[0:num_words * 2]):
            total += chunk
        # Add any left over byte
        if len % 2:
            total += data[-1] << 8
        # Fold 32-bits into 16-bits
        total = (total >> 16) + (total & 0xffff)
        total += total >> 16
        return ~total + 0x10000 & 0xffff

    def sdn_ip_checksum(self, msg, len):
        sum = self.chksum(0, msg, len)
        result = 0
        if (sum == 0):
            result = 0xffff
        else:
            result = struct.pack(">i", sum)
        return result

    def process_na_packet(self, pkt):
        length = pkt.tlen-SDN_IPH_LEN
        # We first check the integrity of the entire SDN NA packet
        if (self.sdn_ip_checksum(pkt.payload, length) != 0xffff):
            logger.warning("bad NA checksum")
            return
        # Parse sdn NA packet
        pkt = NA_Packet.unpack(pkt.payload, length)
        logger.debug(repr(pkt))
        # If the reported payload length in the sdn NA header does not match the packet size,
        # then we drop the packet.
        if (len(pkt.payload) < pkt.payload_len):
            logger.warning("NA packet shorter than reported in the header")
            return
        # sdn IP packet succeed
        logger.debug("succeed unpacking SDN NA packet")
        return pkt
