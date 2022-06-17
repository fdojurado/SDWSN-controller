import sys
import argparse
import multiprocessing as mp
from sdwsn_serial import serial


def socket_connect(host, port, send, rcv):
    print(f'socket connection to {host} and port {port}')
    return serial.SerialBus(host, port, send, rcv)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', type=str, default='127.0.0.1',
                        help='socket address')
    parser.add_argument('-p', '--port', type=int, default=60001,
                        help='socket port')

    args = parser.parse_args()
    print(f'arg: {args}')

    # Run serial port to Cooja
    socket_send = mp.Queue()
    socket_rcv = mp.Queue()
    socket_cooja = socket_connect(
        args.socket, args.port, socket_send, socket_rcv)

    """ Let's start all processes """

    # Serial interface
    if socket_cooja.result != 0:
        print("error connecting to socket")
    else:
        socket_cooja.daemon = True
        socket_cooja.start()

    while True:
        if not socket_rcv.empty():
            print(f'there is something in serial interface')


if __name__ == '__main__':
    main()
    sys.exit(0)
