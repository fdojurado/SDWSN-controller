import sys
import argparse
import multiprocessing as mp
from sdwsn_serial import serial


def socket_connect(host, port, rcv, send):
    print(f'socket connection to {host} and port {port}')
    return serial.SerialBus(host, port, rcv, send)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', type=str, default='127.0.0.1',
                        help='socket address')
    parser.add_argument('-p', '--port', type=str, default='60001',
                        help='socket port')

    args = parser.parse_args()
    print(f'arg: {args}')

    # Run serial port to Cooja
    socket_send = mp.Queue()
    socket_rcv = mp.Queue()
    socket_cooja = socket_connect(
        args.socket, args.port, socket_rcv, socket_send)

    """ Let's start all processes """
    socket_cooja.daemon = True
    socket_cooja.start()


if __name__ == '__main__':
    main()
    sys.exit(0)
