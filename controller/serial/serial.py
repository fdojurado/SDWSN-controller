import socket
import sys
# import logging
from controller import Message
from typing import Optional
from time import time
from datetime import datetime
import multiprocessing as mp

# logger = logging.getLogger('can.serial')

# try:
#     import serial
# except ImportError:
#     logger.warning(
#         "You won't be able to use the serial can backend without "
#         "the serial module installed!"
#     )
#     serial = None

try:
    from serial.tools import list_ports
except ImportError:
    list_ports = None


class SerialBus(mp.Process):
    def __init__(self, config, verbose, input_queue, output_queue):
        mp.Process.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.config = config
        self.verbose = verbose
        self.byte_msg = bytearray()
        self.overflow = 0
        self.escape_character = 0
        self.frame_start = 0
        self.frame_length = 0
        # Serial interface
        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.config.serial.host, self.config.serial.port)
        result = self.ser.connect_ex(server_address)
        if (result != 0):
            print("error connecting to serial port")

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
            if rx_byte and ord(rx_byte) != 0x7E:
                if(self.escape_character):
                    self.escape_character = 0
                    a = int.from_bytes(rx_byte, 'big')
                    b = int.from_bytes(b'\x20', 'big')
                    rx_byte = a ^ b
                    rx_byte = rx_byte.to_bytes(1, 'big')
                elif(rx_byte and ord(rx_byte) == 0x7D):
                    self.escape_character = 1
                    return 0

                if (self.frame_length < (122 + 2)):
                    # Adding 2 bytes from serial communication
                    self.byte_msg.extend(rx_byte)
                    self.frame_length = self.frame_length + 1
                else:
                    self.overflow = 1
                    # print("Packet size overflow: %u bytes\n", self.frame_length)
                    return 0
            else:
                # print("FRAME_BOUNDARY_OCTET detected")
                if (self.escape_character == 1):
                    # print("serial: escape_character == true")
                    self.escape_character = 0
                elif (self.overflow):
                    # print("serial overflow")
                    self.overflow = 0
                    self.frame_length = 0
                    self.frame_start = 1
                    self.byte_msg = bytearray()
                elif (self.frame_length >= 6 and self.frame_start):
                    # Wake up consumer process
                    # print("Wake up consumer process")
                    self.frame_start = 0
                    self.overflow = 0
                    self.frame_length = 0
                    msg_buffer = self.byte_msg
                    self.byte_msg = bytearray()
                    return msg_buffer
                else:
                    # re-synchronization. Start over
                    # print("serial re-synchronization\n")
                    self.frame_start = 1
                    self.byte_msg = bytearray()
                    self.frame_length = 0
                    return 0
                return 0

        except socket.error as e:
            return None

        return 0

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
            msg = self._recv_internal(timeout=time_left)
            if (msg != 0):
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

    def send(self, data):
        """
        Send a message over the serial device.
        """
        print('Sending message over the serial interface')
        byte_msg = bytearray()
        byte_msg.extend(bytes.fromhex('7E'))
        data = [data[i:i+1] for i in range(len(data))]
        for i in range(0, len(data)):
            # print('data')
            # print((data[i]))
            self.check_byte(byte_msg, data[i])
        byte_msg.extend(bytes.fromhex('7E'))
        # print('packet to send')
        # print(byte_msg.hex())
        self.ser.send(byte_msg)

    def check_byte(self, byte_data, data):
        if (ord(data) == 0x7E or ord(data) == 0x7D):
            byte_data.extend(bytes.fromhex('7D'))
            invert = ord(data) ^ ord(b'\x20')
            invert_bytes = invert.to_bytes(len(data), sys.byteorder)
            byte_data.extend(invert_bytes)
        else:
            byte_data.extend(data)

    def run(self):
        while(1):
            # look for incoming  request
            if not self.input_queue.empty():
                # print("incoming queue request")
                data = self.input_queue.get()
                # print(data)
                # send serial packet
                self.send(data)
            try:
                msg = self.recv(0.1)
                if(len(msg) > 0):
                    # send it back to main
                    self.output_queue.put(msg)
            except TypeError:
                pass
