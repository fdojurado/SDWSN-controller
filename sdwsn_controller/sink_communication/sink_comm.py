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

import socket
import sys
# import logging
from sdwsn_controller.sink_communication.sink_abc import SinkABC
import logging

logger = logging.getLogger('main.'+__name__)


class SinkComm(SinkABC):
    def __init__(
        self,
        host: str = '127.0.0.1',
        port: int = 60001
    ):
        assert isinstance(host, str)
        assert isinstance(port, int)
        self.host = host
        self.port = port
        self.byte_msg = bytearray()
        self.overflow = 0
        self.escape_character = 0
        self.frame_start = 0
        self.frame_length = 0
        self.msg = None
        self.ser = None

    def connect(self):
        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.host, self.port)
        self.result = self.ser.connect_ex(server_address)
        return self.result

    def decodeByte(self, n):
        data = bytearray()
        scape_char = 0
        while len(data) < n:
            packet = self.ser.recv(n - len(data))
            if not packet:
                return None
            for byte in packet:
                if scape_char == 1:
                    scape_char = 0
                    int_packet = byte ^ (0x20)
                    byte = int_packet
                    data.extend(bytes([byte]))
                elif byte == 0x7D:
                    scape_char = 1
                else:
                    data.extend(bytes([byte]))
        return data

    def _recv_internal(self, timeout):
        """
        Read a message from the sink.

        Args:
            timeout (_type_):  Seconds to wait for a message.

        Returns:
            int, Message: Message received.
        """
        try:
            # ser.read can return an empty string
            # or raise a SerialException
            rx_byte = self.ser.recv(1)
            # logger.info("rx_byte")
            # logger.info(rx_byte)
            if rx_byte and ord(rx_byte) != 0x7E:
                if (self.escape_character):
                    self.escape_character = 0
                    a = int.from_bytes(rx_byte, 'big')
                    b = int.from_bytes(b'\x20', 'big')
                    rx_byte = a ^ b
                    rx_byte = rx_byte.to_bytes(1, 'big')
                elif (rx_byte and ord(rx_byte) == 0x7D):
                    self.escape_character = 1
                    return 0

                if (self.frame_length < (122 + 2)):
                    # Adding 2 bytes from serial communication
                    self.byte_msg.extend(rx_byte)
                    self.frame_length = self.frame_length + 1
                else:
                    self.overflow = 1
                    # logger.info("Packet size overflow: %u bytes\n",
                    #   self.frame_length)
                    return 0
            else:
                # logger.info("FRAME_BOUNDARY_OCTET detected")
                if (self.escape_character == 1):
                    # logger.info("serial: escape_character == true")
                    self.escape_character = 0
                elif (self.overflow):
                    # logger.info("serial overflow")
                    self.overflow = 0
                    self.frame_length = 0
                    self.frame_start = 1
                    self.byte_msg = bytearray()
                elif (self.frame_length >= 6 and self.frame_start):
                    # Wake up consumer process
                    # logger.info("Wake up consumer process")
                    self.frame_start = 0
                    self.overflow = 0
                    self.frame_length = 0
                    msg_buffer = self.byte_msg
                    self.byte_msg = bytearray()
                    return msg_buffer, False
                else:
                    # re-synchronization. Start over
                    # logger.info("serial re-synchronization\n")
                    self.frame_start = 1
                    self.byte_msg = bytearray()
                    self.frame_length = 0
                    return 0
                return 0

        except socket.error:
            return None

        return 0

    def send(self, data):
        """
        Transmit a message to the sink

        Args:
            data (Message): Message object to transmit.
        """
        logger.debug('Sending message over the serial interface')
        byte_msg = bytearray()
        byte_msg.extend(bytes.fromhex('7E'))
        data = [data[i:i+1] for i in range(len(data))]
        for i in range(0, len(data)):
            # logger.info('data')
            # logger.info((data[i]))
            self.check_byte(byte_msg, data[i])
        byte_msg.extend(bytes.fromhex('7E'))
        logger.debug('packet to send')
        logger.debug(byte_msg.hex())
        self.ser.send(byte_msg)

    def check_byte(self, byte_data, data):
        if (ord(data) == 0x7E or ord(data) == 0x7D):
            byte_data.extend(bytes.fromhex('7D'))
            invert = ord(data) ^ ord(b'\x20')
            invert_bytes = invert.to_bytes(len(data), sys.byteorder)
            byte_data.extend(invert_bytes)
        else:
            byte_data.extend(data)

    def empty_socket(self):
        try:
            while self.recv(0.1):
                pass
        except TypeError:
            pass

    def shutdown(self) -> None:
        """
        Close the serial interface.
        """
        if self.ser is not None:
            self.empty_socket()
            logger.debug("socket buffer is now empty, we close ...")
            self.ser.close()
            # self.ser.shutdown(socket.SHUT_RDWR)

    # def read(self):
    #     while(1):
    #         try:
    #             msg = self.recv(0.1)
    #             if(len(msg) > 0):
    #                 # send it back to main
    #                 self.msg = msg
    #                 # self.output_queue.put(msg)
    #         except TypeError:
    #             pass
