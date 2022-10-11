import socket
import sys
# import logging
from sdwsn_controller.bus import BusABC
import logging

logger = logging.getLogger(__name__)


class SerialBus(BusABC):
    def __init__(self, host: str = '127.0.0.1', port: int = 60001):
        self.host = host
        self.port = port
        self.byte_msg = bytearray()
        self.overflow = 0
        self.escape_character = 0
        self.frame_start = 0
        self.frame_length = 0
        self.msg = None
        self.ser = None

    def connect(self):
        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.host, self.port)
        self.result = self.ser.connect_ex(server_address)
        return self.result

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
            # logger.info("rx_byte")
            # logger.info(rx_byte)
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
                    # logger.info("Packet size overflow: %u bytes\n", self.frame_length)
                    return 0
            else:
                # logger.info("FRAME_BOUNDARY_OCTET detected")
                if (self.escape_character == 1):
                    # logger.info("serial: escape_character == true")
                    self.escape_character = 0
                elif (self.overflow):
                    # logger.info("serial overflow")
                    self.overflow = 0
                    self.frame_length = 0
                    self.frame_start = 1
                    self.byte_msg = bytearray()
                elif (self.frame_length >= 6 and self.frame_start):
                    # Wake up consumer process
                    # logger.info("Wake up consumer process")
                    self.frame_start = 0
                    self.overflow = 0
                    self.frame_length = 0
                    msg_buffer = self.byte_msg
                    self.byte_msg = bytearray()
                    return msg_buffer, False
                else:
                    # re-synchronization. Start over
                    # logger.info("serial re-synchronization\n")
                    self.frame_start = 1
                    self.byte_msg = bytearray()
                    self.frame_length = 0
                    return 0
                return 0

        except socket.error as e:
            return None

        return 0

    def send(self, data):
        """
        Send a message over the serial device.
        """
        logger.info('Sending message over the serial interface')
        byte_msg = bytearray()
        byte_msg.extend(bytes.fromhex('7E'))
        data = [data[i:i+1] for i in range(len(data))]
        for i in range(0, len(data)):
            # logger.info('data')
            # logger.info((data[i]))
            self.check_byte(byte_msg, data[i])
        byte_msg.extend(bytes.fromhex('7E'))
        logger.debug('packet to send')
        logger.debug(byte_msg.hex())
        self.ser.send(byte_msg)

    def check_byte(self, byte_data, data):
        if (ord(data) == 0x7E or ord(data) == 0x7D):
            byte_data.extend(bytes.fromhex('7D'))
            invert = ord(data) ^ ord(b'\x20')
            invert_bytes = invert.to_bytes(len(data), sys.byteorder)
            byte_data.extend(invert_bytes)
        else:
            byte_data.extend(data)

    def empty_socket(self):
        try:
            while self.recv(0.1):
                pass
        except:
            pass

    def shutdown(self) -> None:
        """
        Close the serial interface.
        """
        if self.ser is not None:
            self.empty_socket()
            logger.info("socket buffer is now empty, we close ...")
            self.ser.close()
            # self.ser.shutdown(socket.SHUT_RDWR)

    # def read(self):
    #     while(1):
    #         try:
    #             msg = self.recv(0.1)
    #             if(len(msg) > 0):
    #                 # send it back to main
    #                 self.msg = msg
    #                 # self.output_queue.put(msg)
    #         except TypeError:
    #             pass
