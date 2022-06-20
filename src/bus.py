from abc import ABC
import imp
from typing import cast, Any, Iterator, List, Optional, Sequence, Tuple, Union
from time import time

from abc import ABC, abstractmethod
import logging

LOG = logging.getLogger(__name__)


class BusABC(ABC):

    #: Log level for received messages
    RECV_LOGGING_LEVEL = 9

    @abstractmethod
    def __init__(
        self,
        **kwargs: object
    ):
        pass

    def recv(self, timeout: Optional[float] = None):
        """Block waiting for a message from the Bus.
        :param timeout:
            seconds to wait for a message or None to wait indefinitely
        :return:
            None on timeout or a :class:`Message` object.
        :raises can.CanError:
            if an error occurred while reading
        """
        start = time()
        time_left = timeout

        while True:
            msg, _ = self._recv_internal(timeout=time_left)
            if (msg != 0):
                LOG.log(self.RECV_LOGGING_LEVEL, "Received: %s", msg)
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

    def _recv_internal(
        self, timeout: Optional[float]
    ):
        """
        Read a message from the bus and tell whether it was filtered.
        This methods may be called by :meth:`~can.BusABC.recv`
        to read a message multiple times if the filters set by
        :meth:`~can.BusABC.set_filters` do not match and the call has
        not yet timed out.

        New implementations should always override this method instead of
        :meth:`~can.BusABC.recv`, to be able to take advantage of the
        software based filtering provided by :meth:`~can.BusABC.recv`
        as a fallback. This method should never be called directly.

        .. note::

            This method is not an `@abstractmethod` (for now) to allow older
            external implementations to continue using their existing
            :meth:`~can.BusABC.recv` implementation.

        .. note::

            The second return value (whether filtering was already done) may
            change over time for some interfaces, like for example in the
            Kvaser interface. Thus it cannot be simplified to a constant value.

        :param float timeout: seconds to wait for a message,
                              see :meth:`~can.BusABC.send`

        :return:
            1.  a message that was read or None on timeout
            2.  a bool that is True if message filtering has already
                been done and else False

        :raises can.CanOperationError: If an error occurred while reading
        :raises NotImplementedError:
            if the bus provides it's own :meth:`~can.BusABC.recv`
            implementation (legacy implementation)

        """
        raise NotImplementedError("Trying to read from a write only bus?")

    @abstractmethod
    def send(self, msg, timeout: Optional[float] = None) -> None:
        """Transmit a message to the CAN bus.

        Override this method to enable the transmit path.

        :param Message msg: A message object.

        :param timeout:
            If > 0, wait up to this many seconds for message to be ACK'ed or
            for transmit queue to be ready depending on driver implementation.
            If timeout is exceeded, an exception will be raised.
            Might not be supported by all interfaces.
            None blocks indefinitely.

        :raises can.CanOperationError: If an error occurred while sending
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
