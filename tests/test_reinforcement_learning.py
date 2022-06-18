import sys
import argparse
import multiprocessing as mp
from time import sleep

from sdwsn_common import common

from sdwsn_packet import packet_dissector

from sdwsn_common import globals

from sdwsn_serial.serial import SerialBus

from sdwsn_resource_manager import resource_manager

from sdwsn_controller.controller import Controller

from sdwsn_database.database import Database


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', type=str, default='127.0.0.1',
                        help='socket address')
    parser.add_argument('-p', '--port', type=int, default=60001,
                        help='socket port')
    parser.add_argument('-db', '--db', type=str, default='127.0.0.1',
                        help='Database address')
    parser.add_argument('-dbp', '--dbPort', type=int, default=27017,
                        help='Database port')

    args = parser.parse_args()

    print(args)

    # Initialize global variables
    globals.globals_initialize()

    # Create an instance of the controller
    controller = Controller()
    # Create a serial interface instance
    serial_interface = SerialBus(args.socket, args.port)
    # Add it to the controller
    controller.serial = serial_interface
    # Create an instance of the Database
    myDB = Database('mySDN', args.db, args.dbPort)
    # Add it to the controller
    controller.db = myDB
    # Create an instance of the packet dissector
    myPacketDissector = packet_dissector.PacketDissector('MyDissector', myDB, None)
    # Add it to the controller
    controller.packet_dissector = myPacketDissector
    # Start the controller
    controller.daemon = True
    controller.start()

    while True:
        sleep(0.1)


if __name__ == '__main__':
    main()
    sys.exit(0)
