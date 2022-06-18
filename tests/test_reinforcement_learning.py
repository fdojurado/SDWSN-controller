import sys
import argparse
import multiprocessing as mp

from sdwsn_common import common

from sdwsn_packet import packet_dissector

from sdwsn_common import globals

import sdwsn_serial

from sdwsn_resource_manager import resource_manager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', type=str, default='127.0.0.1',
                        help='socket address')
    parser.add_argument('-p', '--port', type=int, default=60001,
                        help='socket port')

    args = parser.parse_args()

    # Initialize global variables
    globals.globals_initialize()

    # Create a resource manager
    resources = resource_manager.ResourceManager()
    # All resources run in an independent multiprocessing module
    # Add Cooja simulator as a resource
    # cooja_component =resource_manager.ResourceComponent(
    #     name='cooja', init_func=sdwsn_serial.serial.serial_init, host=args.socket, port=args.port)
    # Add serial interface to the resource manager
    serial_component = resource_manager.ResourceComponent(
        name='serial', init_func=sdwsn_serial.serial.serial_init, host=args.socket, port=args.port)
    resources.add(serial_component)

    """ Let's start all processes """
    if not resources.start():
        print("fail to start, exiting")
        return



if __name__ == '__main__':
    main()
    sys.exit(0)
