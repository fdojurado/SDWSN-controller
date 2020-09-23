import socket
import sys

from controller import Message


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

    def connect(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (self.host, self.port)
        print('connecting to %s port %s' % server_address)
        sock.connect(server_address)
        # buffer = ''
        # try:
        #     # Look for the response
        #     while True:
        #         data = sock.recv(1024)
        #         print(data)
        #         stringdata = data.decode('utf-8')
        #         buffer += stringdata
        #         if not buffer:
        #             break
        #         if not buffer.endswith("\n"):
        #             continue
        #         if buffer.endswith("\n"):
        #             print(buffer, end='')
        #             buffer = ''
        #     print(ex)
        # except KeyboardInterrupt as ex:
        #     print(ex)
        # except:
        #     print(sys.exc_info())
        # finally:
        #     print('closing socket')
        #     sock.close()
