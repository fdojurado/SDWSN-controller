import socket
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
        except serial.SerialException:
            return None

        if rx_byte and ord(rx_byte) == 0x7E:
            addr = self.decodeByte(2)
            message_type = ord(self.decodeByte(1))
            payload_len = ord(self.decodeByte(1))-6
            reserved0 = ord(self.decodeByte(1))
            reserved1 = ord(self.decodeByte(1))
            data = self.decodeByte(payload_len)
            rxd_byte = ord(self.ser.recv(1))
            if rxd_byte == 0x7E:
                # received message data okay
                msg = Message(
                    addr=addr,
                    message_type=message_type,
                    payload_len=payload_len,
                    reserved0=reserved0,
                    reserved1=reserved1,
                    data=data,
                )
                return msg

        else:
            return None

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
            if msg is not None:
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
        byte_msg.append(0x7E)

        for i in range(0, len(data)):
            # print('msg.data')
            # print(msg.data[i])
            self.check_byte(byte_msg, data[i])
        byte_msg.append(0x7E)
        # print('packet to send')
        # print(byte_msg.hex())
        self.ser.send(byte_msg)

    def check_byte(self, byte_data, data):
        if (data == 0x7E or data == 0x7D):
            byte_data.append(0x7D)
            invert = data ^ (0x20)
            byte_data.append(invert)
        else:
            byte_data.append(data)

    def run(self):
        msg = Message()
        while(1):
            # look for incoming  request
            if not self.input_queue.empty():
                print("incoming queue request")
                data = self.input_queue.get()
                print(data)
                # send serial packet
                self.send(data)
            try:
                msg = self.recv(0.1)
                if msg is not None:
                    # send it back to main
                    self.output_queue.put(msg)
            except TypeError:
                pass
