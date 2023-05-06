#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from fit_iot_lab import common
import os
import argparse
import logging
from rich.logging import RichHandler


# Create logger
logger = logging.getLogger(__name__)

# get the path of this example
SELF_PATH = os.path.dirname(os.path.abspath(__file__))
# move three levels up
ELISE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(SELF_PATH)))
ARCH_PATH = os.path.normpath(os.path.join(
    ELISE_PATH, "iot-lab-contiki-ng", "arch"))
CONTIKI_PATH = os.path.normpath(os.path.join(ELISE_PATH, "contiki-ng"))


def main():
    parser = argparse.ArgumentParser(
        description='This submits a experiment to the FIT-IoT LAB.')

    parser.add_argument('username', type=str,
                        help='Username')
    parser.add_argument('password', type=str,
                        help='Password')
    parser.add_argument('node_list', nargs='+',
                        help='Sensor nodes list, the first node is assigned to the sink')

    parser.add_argument('-pt', '--platform-target', type=str,
                        default='iotlab', help='Sensor platform to use')
    parser.add_argument('-t', '--time', type=int,
                        default=10, help='Length in minutes of the experiment')
    parser.add_argument('-s', '--site', type=str,
                        default='grenoble', help='FIT IoT LAB site')
    parser.add_argument('-b', '--board', type=str,
                        default='m3', help='Sensor board name')
    parser.add_argument('-e', '--end-node', type=str,
                        default='/examples/sdn-tsch-node/', help='Path, within Contiki folder, to the end node example')
    parser.add_argument('-c', '--controller', type=str,
                        default='/examples/sdn-tsch-sink/', help='Path, within Contiki folder, to sink example')
    parser.add_argument('-dbg', '--debug_level', default='NOTSET',
                        help='Debug level, default NOTSET.')
    parser.add_argument('-hp', '--home-port', type=int,
                        default=2000, help='home port')
    # Arguments for Contiki
    parser.add_argument('-p', '--target-port', type=int, default=20000,
                        help='target port')

    args = parser.parse_args()

    assert args.debug_level in ['CRITICAL',
                                'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'], "Incorrect debug level"
    # Set debug level
    logging.basicConfig(
        level=args.debug_level,
        format='%(asctime)s - %(message)s',
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    # Compile firmware
    firmware_dir = os.path.normpath(os.path.join(
        SELF_PATH, "firmware"))
    logger.info(f'firmware folder: {firmware_dir}')
    os.makedirs(firmware_dir, exist_ok=True)
    # The NODE ID for the end node starts with 2.
    N = len(args.node_list)
    count = 2
    app = CONTIKI_PATH+args.end_node
    while (count <= N):
        node_id = count
        common.compile_firmware(firmware_dir, ARCH_PATH, 'sdn-tsch-node.iotlab', app,
                                args.platform_target, str(0), args.board, str(node_id))
        count += 1

    # We now build the `tsch-sdn-controller` application
    app = CONTIKI_PATH+args.controller
    common.compile_firmware(firmware_dir, ARCH_PATH, 'sdn-tsch-sink.iotlab', app,
                            args.platform_target, str(0), args.board, str(1))

    return args, firmware_dir


if __name__ == "__main__":
    arguments, firmware_dir = main()
    common.launch_iotlab(arguments, firmware_dir)
