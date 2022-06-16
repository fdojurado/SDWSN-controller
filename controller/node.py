from typing import Optional, Union

from controller import typechecking

from math import isinf, isnan


class Node:
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
        "addr",
        "energy",
        "rank",
        "prev_ranks",
        "next_ranks",
        "total_ranks",
        "total_nb",
        "alive",
    )

    def __init__(
        self,
        addr: str = 0,
        energy: int = 0,
        rank: int = 0,
        prev_ranks: int = 0,
        next_ranks: int = 0,
        total_ranks: int = 0,
        total_nb: int = 0,
        alive: int = 0,
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
        self.addr = addr
        self.energy = energy
        self.rank = rank
        self.prev_ranks = prev_ranks
        self.next_ranks = next_ranks
        self.total_ranks = total_ranks
        self.total_nb = total_nb
        self.alive = alive

        if check:
            self._check()

    def _check(self):
        """Checks if the message parameters are valid.
        Assumes that the types are already correct.

        :raises ValueError: iff one or more attributes are invalid
        """

        if self.rank >= 0:
            raise ValueError("rank invalid")
        if isinf(self.rank):
            raise ValueError("rank may not be infinite")
        if isnan(self.rank):
            raise ValueError("rank may not be NaN")

        if self.prev_ranks >= 0:
            raise ValueError("prev_ranks invalid")
        if isinf(self.prev_ranks):
            raise ValueError("prev_ranks may not be infinite")
        if isnan(self.prev_ranks):
            raise ValueError("prev_ranks may not be NaN")

        if self.next_ranks >= 0:
            raise ValueError("next_ranks invalid")
        if isinf(self.next_ranks):
            raise ValueError("next_ranks may not be infinite")
        if isnan(self.next_ranks):
            raise ValueError("next_ranks may not be NaN")

        if self.total_ranks >= 0:
            raise ValueError("total_ranks invalid")
        if isinf(self.total_ranks):
            raise ValueError("total_ranks may not be infinite")
        if isnan(self.total_ranks):
            raise ValueError("total_ranks may not be NaN")

        if self.total_nb >= 0:
            raise ValueError("total_nb invalid")
        if isinf(self.total_nb):
            raise ValueError("total_nb may not be infinite")
        if isnan(self.total_nb):
            raise ValueError("total_nb may not be NaN")

        if self.alive >= 0:
            raise ValueError("alive invalid")
        if isinf(self.alive):
            raise ValueError("alive may not be infinite")
        if isnan(self.alive):
            raise ValueError("alive may not be NaN")

    def print_packet(self):
        print("addr:"+self.addr)
        energy = str(self.energy)
        print("energy:"+energy)
        rank = str(self.rank)
        print("rank:"+rank)
        prev_ranks = str(self.prev_ranks)
        print("prev_ranks:"+prev_ranks)
        next_ranks = str(self.next_ranks)
        print("next_ranks:"+next_ranks)
        total_ranks = str(self.total_ranks)
        print("total_ranks:"+total_ranks)
        total_nb = str(self.total_nb)
        print("total_nb:"+total_nb)
        alive = str(self.alive)
        print("alive:"+alive)
        
        return 0