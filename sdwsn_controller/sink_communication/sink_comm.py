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

from sdwsn_controller.sink_communication.sink_abc import SinkABC

import logging
import socket

logger = logging.getLogger(f'main.{__name__}')


class SinkComm(SinkABC):
    def __init__(
        self,
        config
    ):
        assert isinstance(config.sink_comm.host_dev, str)
        assert isinstance(config.sink_comm.port_baud, int)
        self.host = config.sink_comm.host_dev
        self.port = config.sink_comm.port_baud
        self.__name = "Socket"
        self.ser = None
        super().__init__()

    @property
    def name(self):
        return self.__name

    @property
    def ser(self):
        return self.__ser

    @ser.setter
    def ser(self, ser):
        self.__ser = ser

    def connect(self):
        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.host, self.port)
        self.result = self.ser.connect_ex(server_address)
        return self.result

    def read_byte(self):
        return self.ser.recv(1)

    def error_exception(self):
        return socket.error

    def send_stream_bytes(self, stream_bytes):
        self.ser.send(stream_bytes)
