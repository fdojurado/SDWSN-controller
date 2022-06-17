import sys
import argparse
import multiprocessing as mp

from sdwsn_common import common

from sdwsn_packet import packet_dissector

from sdwsn_common import globals

from sdwsn_controller.network_config.network_config import NetworkConfig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', type=str, default='127.0.0.1',
                        help='socket address')
    parser.add_argument('-p', '--port', type=int, default=60001,
                        help='socket port')

    args = parser.parse_args()
    
    # Initialize global variables
    globals.globals_initialize()

    # Run serial port to Cooja
    socket_send = mp.Queue()
    socket_rcv = mp.Queue()
    socket_cooja = common.socket_connect(
        args.socket, args.port, socket_send, socket_rcv)

    # Initialize network configuration process


    """ Let's start all processes """

    # Serial interface
    if socket_cooja.result != 0:
        print("error connecting to socket")
    else:
        socket_cooja.daemon = True
        socket_cooja.start()

    while True:
        if not socket_rcv.empty():
            data = common.get_data_from_mqueue(socket_rcv)
            packet_dissector.handle_serial_packet(data)


if __name__ == '__main__':
    main()
    sys.exit(0)
