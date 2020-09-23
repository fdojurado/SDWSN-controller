from typing import Optional, Union

from controller import typechecking

from math import isinf, isnan


class Message:
    """
    The :class:`~can.Message` object is used to represent CAN messages for
    sending, receiving and other purposes like converting between different
    logging formats.

    Messages can use extended identifiers, be remote or error frames, contain
    data and may be associated to a channel.

    Messages are always compared by identity and never by value, because that
    may introduce unexpected behaviour. See also :meth:`~can.Message.equals`.

    :func:`~copy.copy`/:func:`~copy.deepcopy` is supported as well.

    Messages do not support "dynamic" attributes, meaning any others than the
    documented ones, since it uses :attr:`~object.__slots__`.
    """

    __slots__ = (
        "addr0",
        "addr1",
        "message_type",
        "payload_len",
        "reserved0",
        "reserved1",
        "data",
    )

    def __init__(
        self,
        addr0: int = 0,
        addr1: int = 0,
        message_type: int = 0,
        payload_len: int = 0,
        reserved0: int = 0,
        reserved1: int = 0,
        data: Optional[typechecking.SerialData] = None,
        check: bool = False,
    ):
        """
        To create a message object, simply provide any of the below attributes
        together with additional parameters as keyword arguments to the constructor.

        :param check: By default, the constructor of this class does not strictly check the input.
                      Thus, the caller must prevent the creation of invalid messages or
                      set this parameter to `True`, to raise an Error on invalid inputs.
                      Possible problems include the `dlc` field not matching the length of `data`
                      or creating a message with both `is_remote_frame` and `is_error_frame` set to `True`.

        :raises ValueError: iff `check` is set to `True` and one or more arguments were invalid
        """
        self.addr0 = addr0
        self.addr1 = addr1
        self.message_type = message_type
        self.payload_len = payload_len
        self.reserved0 = reserved0
        self.reserved1 = reserved1

        if data is None:
            self.data = bytearray()
        elif isinstance(data, bytearray):
            self.data = data
        else:
            try:
                self.data = bytearray(data)
            except TypeError:
                err = "Couldn't create message from {} ({})".format(
                    data, type(data))
                raise TypeError(err)

        if payload_len is None:
            self.payload_len = len(self.data)
        else:
            self.payload_len = payload_len

        if check:
            self._check()

    def _check(self):
        """Checks if the message parameters are valid.
        Assumes that the types are already correct.

        :raises ValueError: iff one or more attributes are invalid
        """

        if self.addr0 < 0 or self.addr0 > 255:
            raise ValueError("addr0 invalid")
        if isinf(self.addr0):
            raise ValueError("addr0 may not be infinite")
        if isnan(self.addr0):
            raise ValueError("addr0 may not be NaN")

        if self.addr1 < 0 or self.addr1 > 255:
            raise ValueError("addr1 invalid")
        if isinf(self.addr1):
            raise ValueError("addr1 may not be infinite")
        if isnan(self.addr1):
            raise ValueError("addr1 may not be NaN")

        if self.message_type < 0:
            raise ValueError("message_type may not be negative")
        if isinf(self.message_type):
            raise ValueError("message_type may not be infinite")
        if isnan(self.message_type):
            raise ValueError("message_type may not be NaN")

        if self.payload_len < 0:
            raise ValueError("payload_len may not be negative")
        if isinf(self.payload_len):
            raise ValueError("payload_len may not be infinite")
        if isnan(self.payload_len):
            raise ValueError("payload_len may not be NaN")

    def __bytes__(self) -> bytes:
        return bytes(self.data)

    def __copy__(self) -> "Message":
        new = Message(
            addr0=self.addr0,
            addr1=self.addr1,
            message_type=self.message_type,
            payload_len=self.payload_len,
            reserved0=self.reserved0,
            reserved1=self.reserved1,
            data=self.data,
        )
        return new
