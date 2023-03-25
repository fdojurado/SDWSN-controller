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

from abc import ABC, abstractmethod

from typing import Optional

from time import time

import logging

import sys


logger = logging.getLogger(__name__)


class SinkABC(ABC):

    @abstractmethod
    def __init__(
        self
    ):
        """
        Abstract class for sink communication.
        """
        self.byte_msg = bytearray()
        self.overflow = 0
        self.escape_character = 0
        self.frame_start = 0
        self.frame_length = 0
        self.msg = None

    @abstractmethod
    def name(self):
        """
        Get the name of the sink.

        Returns:
            str: Name of the sink.
        """
        pass

    @property
    @abstractmethod
    def ser(self):
        """
        Get the serial object.

        Returns:
            serial: Serial object.
        """
        pass

    @abstractmethod
    def connect(self, **kwargs):
        """
        Connect to the sink.
        """
        pass

    @abstractmethod
    def read_byte(self):
        """
        Read a byte from the sink.

        Returns:
            int: Byte read.
        """
        pass

    @abstractmethod
    def error_exception(self):
        """
        Check if there is an error in the sink.

        Returns:
            int: Error code.
        """
        pass

    @abstractmethod
    def send_stream_bytes(self, stream_bytes):
        """
        Send a stream of bytes to the sink.

        Args:
            stream_bytes (bytes): Bytes to send.
        """
        pass

    def _recv_internal(self):
        """
        Read a message from the sink.

        Returns:
            int, Message: Message received.
        """
        try:
            # ser.read can return an empty string
            # or raise a SerialException
            rx_byte = self.read_byte()
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

        except self.error_exception():
            return None

        return 0

    def recv(self, timeout: Optional[float] = None) -> Optional[bytearray]:
        """
        Block waiting for a message from the sink.

        Args:
            timeout (Optional[float], optional): Seconds to wait for a message.
                Defaults to None (Wait indefinitely).

        Returns:
            Message, None: Returns message.
        """
        start = time()
        time_left = timeout

        while time_left is None or time_left > 0:
            msg, _ = self._recv_internal()
            if msg != 0:
                # logger.debug("Received: %s", msg)
                return msg
            if timeout is None:
                continue
            else:
                time_left = timeout - (time() - start)

        return None

    def check_byte(self, byte_data, data):
        if (ord(data) == 0x7E or ord(data) == 0x7D):
            byte_data.extend(bytes.fromhex('7D'))
            invert = ord(data) ^ ord(b'\x20')
            invert_bytes = invert.to_bytes(len(data), sys.byteorder)
            byte_data.extend(invert_bytes)
        else:
            byte_data.extend(data)

    def send(self, data) -> None:
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
        self.send_stream_bytes(byte_msg)

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

    def __iter__(self):
        """Allow iteration on messages as they are received.

            >>> for msg in bus:
            ...     print(msg)


        :yields:
            :class:`Message` msg objects.
        """
        while True:
            msg = self.recv(timeout=1.0)
            if msg is not None:
                yield msg
