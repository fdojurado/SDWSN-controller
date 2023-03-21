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

import logging

from time import time
from typing import Optional


logger = logging.getLogger(__name__)


class SinkABC(ABC):

    @abstractmethod
    def __init__(
        self,
        **kwargs: object
    ):
        pass

    def recv(self, timeout: Optional[float] = None):
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

        while True:
            msg, _ = self._recv_internal(timeout=time_left)
            if (msg != 0):
                # logger.debug("Received: %s", msg)
                return msg
            # if not, and timeout is None, try indefinitely
            if timeout is None:
                continue
            # try next one only if there still is time, and with
            # reduced timeout
            else:
                time_left = timeout - (time() - start)
                if time_left > 0:
                    continue
                else:
                    return None

    @abstractmethod
    def _recv_internal(
        self, timeout: Optional[float]
    ):
        """
        Read a message from the sink.

        Args:
            timeout (Optional[float]): Seconds to wait for a message.

        Raises:
            NotImplementedError: Not implemented error.
        """
        raise NotImplementedError("Trying to read from a write only bus?")

    @abstractmethod
    def send(self, msg, timeout: Optional[float] = None) -> None:
        """
        Transmit a message to the sink

        Args:
            msg (Message): Message object to transmit.
            timeout (Optional[float], optional): Wait for up to n seconds
                to the message be acked. Defaults to None.

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError("Trying to write to a readonly bus?")

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
