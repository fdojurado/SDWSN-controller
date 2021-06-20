"""Types for mypy type-checking
"""

import typing

if typing.TYPE_CHECKING:
    import os

# import mypy_extensions

# TODO: Once buffer protocol support lands in typing, we should switch to that,
# since can.message.Message attempts to call bytearray() on the given data, so
# this should have the same typing info.
#
# See: https://github.com/python/typing/issues/593
SerialData = typing.Union[bytes, bytearray, int, typing.Iterable[int]]