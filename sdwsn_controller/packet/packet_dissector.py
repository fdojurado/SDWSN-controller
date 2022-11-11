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
from abc import ABC

import logging

from sdwsn_controller.packet.packet import Data_Packet, NA_Packet
from sdwsn_controller.packet.packet import SerialPacket, SDN_IP_Packet
from sdwsn_controller.packet.packet import serial_protocol, sdn_protocols
from sdwsn_controller.packet.packet import SDN_IPH_LEN

import struct

logger = logging.getLogger('main.'+__name__)


class Dissector(ABC):
    """
    Dissect abstract class. This class makes sure every packet dissector
    has the right constructor - functions.
    """

    def __init__(
        self,
        cycle_sequence,
        sequence,
        database,
        name
    ):
        self.__cycle_sequence = cycle_sequence
        self.__sequence = sequence
        self.__db = database
        self.__name = name
        super().__init__()

    @property
    def name(self):
        return self.__name

    @property
    def sequence(self):
        return self.__sequence

    @sequence.setter
    def sequence(self, num):
        self.__sequence = num

    @property
    def cycle_sequence(self):
        return self.__cycle_sequence

    @cycle_sequence.setter
    def cycle_sequence(self, num):
        self.__cycle_sequence = num

    def reset_pkt_sequence(self):
        self.sequence = 0

    def get_cycle_sequence(self):
        return self.cycle_sequence

    @property
    def db(self):
        if self.__db is not None:
            return self.__db

    def save_energy(self, pkt, na_pkt):
        if self.db is not None:
            self.db.save_energy(pkt, na_pkt)

    def save_neighbors(self, pkt, na_pkt):
        if self.db is not None:
            self.db.save_neighbors(pkt, na_pkt)

    def save_pdr(self, pkt, data_pkt):
        if self.db is not None:
            self.db.save_pdr(pkt, data_pkt)

    def save_delay(self, pkt, data_pkt):
        if self.db is not None:
            self.db.save_delay(pkt, data_pkt)

    def save_serial_packet(self, serial_pkt):
        if self.db is not None:
            self.db.save_serial_packet(serial_pkt.toJSON())


class PacketDissector(Dissector):
    def __init__(
            self,
            cycle_sequence: int = 0,
            sequence: int = 0,
            database: object = None,
    ):
        self.ack_pkt = None
        super().__init__(
            cycle_sequence=cycle_sequence,
            sequence=sequence,
            database=database,
            name="Packet Dissector"
        )

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
                # We now build the energy DB
                self.save_energy(pkt, na_pkt)
                # We now build the neighbors DB
                self.save_neighbors(pkt, na_pkt)
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
                # We now build the pdr DB
                self.save_pdr(pkt, data_pkt)
                # We now build the delay DB
                self.save_delay(pkt, data_pkt)
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
            logger.debug("packet shorter than reported in serial header")
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
