import socket
import sys

from controller import Message
from typing import Optional, Union, Iterator, Tuple
from time import time
import struct
import threading
from datetime import datetime
from controller.database.database import Database
import pandas as pd

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

def process_nodes(msg):
    addr0 = str(msg.addr0)
    addr1 = str(msg.addr1)
    addr = addr0+'.'+addr1
    # print(addr)
    data = msg.data
    # print(data)
    energy = data[0:2]
    energy = socket.htons(int(energy.hex(), 16))
    # print(energy)
    rank = data[2]
    prev_ranks = data[3]
    next_ranks = data[4]
    total_ranks = data[5]
    total_nb = data[6]
    alive = data[7]
    # nodes = Node(addr=addr, energy=energy, rank=rank, prev_ranks=prev_ranks,
    #  next_ranks=next_ranks, total_ranks=total_ranks, total_nb=total_nb, alive=alive)
    # nodes.print_packet()
    data = {
        'time': datetime.now(),
        'energy': energy,
        'rank': rank,
        'prev_ranks': prev_ranks,
        'next_ranks': next_ranks,
        'total_ranks': total_ranks,
        'total_nb': total_nb,
        'alive': alive,
    }
    node = {
        '_id': addr,
        'data': [
            data,
        ]
    }
    if Database.exist("nodes", addr) == 0:
        Database.insert("nodes", node)
    else:
        Database.push_doc("nodes", addr, data)
    Database.print_documents("nodes")
    df = pd.DataFrame()
    print(df)
    # Calling DataFrame constructor on list
    coll = Database.find("nodes", {})
    for x in coll:
        print(x)
        print(x['data'])
        df = pd.DataFrame(x['data'])
        print(df)
        for y in x['data']:
            print(y)

def handle_serial(msg):
    msg.print_packet()
    if(msg.message_type == 2):
        print("nodes' info")
        process_nodes(msg)

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
            raise ValueError("Must specify a serial port.")

        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        # Create a TCP/IP socket

        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.port)
        print('connecting to %s port %s' % server_address)
        self.ser.connect(server_address)
        t1 = threading.Thread(target = self.get_data)
        t1.daemon = True
        t1.start()
    
    def get_data(self):
        """This function serves the purpose of collecting data from the serial object and storing 
        the filtered data into a global variable.
        The function has been put into a thread since the serial event is a blocking function.
        """
        msg = Message()
        while(1):   
            try:
                msg = self.recv(0.1)
                if msg is not None:
                    print('msg')
                    print(msg.addr1)
                    print(msg)
                    handle_serial(msg)
            except TypeError:
                pass

    def send(self, msg, timeout=None):
        """
        Send a message over the serial device.
        """
        byte_msg = bytearray()
        byte_msg.append(0x7E)
        self.check_byte(byte_msg, msg.addr0)
        self.check_byte(byte_msg, msg.addr1)
        self.check_byte(byte_msg, msg.message_type)
        self.check_byte(byte_msg, msg.payload_len)
        self.check_byte(byte_msg, msg.reserved0)
        self.check_byte(byte_msg, msg.reserved1)

        for i in range(0, msg.payload_len):
            # print('msg.data')
            # print(msg.data[i])
            self.check_byte(byte_msg, msg.data[i])
        byte_msg.append(0x7E)
        print('packet to send')
        print(byte_msg.hex())
        self.ser.send(byte_msg)

    def check_byte(self, byte_data, data):
        if (data == 0x7E or data == 0x7D):
            byte_data.append(0x7D)
            invert = data ^ (0x20)
            byte_data.append(invert)
        else:
            byte_data.append(data)

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
                    # print('time_left')
                    continue
                else:
                    print('None')
                    return None

    def decodeByte(self, n):
        data = bytearray()
        scape_char = 0
        while len(data) < n:
            packet = self.ser.recv(n - len(data))
            if not packet:
                return None
            for byte in packet:
                if scape_char == 1:
                    # print('inverting')
                    scape_char = 0
                    int_packet = byte ^ (0x20)
                    byte = int_packet
                    # print(byte)
                    data.extend(bytes([byte]))
                elif byte == 0x7D:
                    # print('escape char found')
                    scape_char = 1
                    # n = n + 1
                else:
                    data.extend(bytes([byte]))
            # print('data')
            # print(data)
        return data

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
            addr0 = ord(self.decodeByte(1))
            print("addr0")
            print(addr0)
            addr1 = ord(self.decodeByte(1))
            print("addr1")
            print(addr1)
            message_type = ord(self.decodeByte(1))
            print("message_type")
            print(message_type)
            payload_len = ord(self.decodeByte(1))
            print("payload_len")
            print(payload_len)
            reserved0 = ord(self.decodeByte(1))
            print("reserved0")
            print(reserved0)
            reserved1 = ord(self.decodeByte(1))
            print("reserved1")
            print(reserved1)

            # if chunk == '':
            #     raise RuntimeError("socket connection broken")
            # chunks.append(chunk)

            data = self.decodeByte(payload_len)

            print('data')
            print(data.hex())

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
