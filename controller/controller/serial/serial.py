import socket
import sys

from controller import Message
from typing import Optional, Union, Iterator, Tuple
from time import time
import struct

try:
    import serial
except ImportError:
    logger.warning(
        "You won't be able to use the serial can backend without "
        "the serial module installed!"
    )
    serial = None

try:
    from serial.tools import list_ports
except ImportError:
    list_ports = None


class SerialBus:

    def __init__(
        self, host, port
    ):
        """
        :param str channel:
            The serial device to open. For example "/dev/ttyS1" or
            "/dev/ttyUSB0" on Linux or "COM1" on Windows systems.

        :param int baudrate:
            Baud rate of the serial device in bit/s (default 115200).

            .. warning::
                Some serial port implementations don't care about the baudrate.

        :param float timeout:
            Timeout for the serial device in seconds (default 0.1).

        :param bool rtscts:
            turn hardware handshake (RTS/CTS) on and off

        """
        self.host = host
        self.port = port

        if not host:
            raise ValueError("Must specify a serial host.")
        if not port:
            raise ValueError("Must specify a serial host.")

        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        # Create a TCP/IP socket

        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.port)
        print('connecting to %s port %s' % server_address)
        self.ser.connect(server_address)

    def recv(self, timeout: Optional[float] = None) -> Optional[Message]:
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

            # try to get a message
            # print('trying getting message')
            msg = self._recv_internal(timeout=time_left)

            if msg is not None:
                return msg

            # if not, and timeout is None, try indefinitely
            if timeout is None:
                print('timeout')
                continue

            # try next one only if there still is time, and with
            # reduced timeout
            else:

                time_left = timeout - (time() - start)

                if time_left > 0:
                    print('time_left')
                    continue
                else:
                    print('None')
                    return None

    def _recv_internal(self, timeout):
        """
        Read a message from the serial device.

        :param timeout:

            .. warning::
                This parameter will be ignored. The timeout value of the channel is used.

        :returns:
            Received message and False (because not filtering as taken place).

            .. warning::
                Flags like is_extended_id, is_remote_frame and is_error_frame
                will not be set over this function, the flags in the return
                message are the default values.

        :rtype:
            Tuple[can.Message, Bool]
        """
        try:
            # ser.read can return an empty string
            # or raise a SerialException
            rx_byte = self.ser.recv(1)
            # print("rx_byte")
            # print(rx_byte)
        except serial.SerialException:
            return None

        if rx_byte and ord(rx_byte) == 0x7E:
            print("start of frame found")
            addr0 = ord(bytearray(self.ser.recv(1)))
            print("addr0")
            print(addr0)
            addr1 = ord(bytearray(self.ser.recv(1)))
            print("addr1")
            print(addr1)
            message_type = ord(bytearray(self.ser.recv(1)))
            print("message_type")
            print(message_type)
            payload_len = ord(bytearray(self.ser.recv(1)))
            print("payload_len")
            print(payload_len)
            reserved0 = ord(bytearray(self.ser.recv(1)))
            print("reserved0")
            print(reserved0)
            reserved1 = ord(bytearray(self.ser.recv(1)))
            print("reserved1")
            print(reserved1)

            # if chunk == '':
            #     raise RuntimeError("socket connection broken")
            # chunks.append(chunk)

            if(payload_len > 0):
                bytes_recd = 0
                data = []
                while bytes_recd < payload_len:
                    dat = self.ser.recv(
                        min(payload_len - bytes_recd, 2048))
                    if dat == '':
                        raise RuntimeError("socket connection broken")
                    print("dat")
                    print(dat)
                    bytes_recd = bytes_recd + len(dat)
                    data.append(ord(dat))
            else:
                data = 0
            
            print('data')
            print(data)

            rxd_byte = ord(self.ser.recv(1))
            if rxd_byte == 0x7E:
                print("correct frame")
                # received message data okay
                msg = Message(
                    addr0=addr0,
                    addr1=addr1,
                    message_type=message_type,
                    payload_len=payload_len,
                    reserved0=reserved0,
                    reserved1=reserved1,
                    data=data,
                )
                return msg

        else:
            return None
