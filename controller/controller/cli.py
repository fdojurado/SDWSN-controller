# import config
# from controller.serial import SerialBus
# from controller.mqtt_client.mqtt_client import sdwsn_mqtt_client
from hashlib import new
from controller.serial.serial_packet_dissector import *
from controller.plotting.plotting import SubplotAnimation
from controller.routing.routing import Routing
from controller.serial.serial import SerialBus
from controller.database.database import Database
from controller.config import ServerConfig, DEFAULT_CONFIG
# from controller.gui.gui import SDNcontrollerapp, f, animate
from controller.message import Message
from controller.node import Node
import socket
# import tkinter as tk
from json import JSONDecodeError
import signal
import sys
import multiprocessing as mp
import time

# from daemon import DaemonContext
from matplotlib import animation
from matplotlib import pyplot as plt
import numpy as np
import networkx as nx
import networkx.algorithms.isomorphism as iso
import random
import pandas as pd
# from networkx.drawing.nx_agraph import graphviz_layout

# device topics
serial_topic = "controller/serial"  # publishing topic

SERVER = {'serial-controller': SerialBus}


def main(command, verbose, version, config, daemon):
    """The main function run by the CLI command.

    Args:
        command (str): The command to run.
        verbose (bool): Use verbose output if True.
        version (bool): Print version information and exit if True.
        config (str): Configuration file.
        daemon (bool): Run as a daemon if True.
    """
    # Define signal handler to cleanly exit the program.

    def exit_process(signal_number, frame):
        # pylint: disable=no-member
        print('Received %s signal. Exiting...',
              signal.Signals(signal_number).name)
        server.stop()
        sys.exit(0)

    # Register signals.
    signal.signal(signal.SIGQUIT, exit_process)
    signal.signal(signal.SIGTERM, exit_process)
    """ Initialise database """
    Database.initialise()
    """ Initialise routing """
    Routing(ServerConfig.from_json_file(config))
    """ Define Queues """
    input_queue = mp.Queue()
    output_queue = mp.Queue()
    """ Start the serial interface in background (as a daemon) """
    sp = SerialBus(ServerConfig.from_json_file(config),
                   verbose, input_queue, output_queue)
    sp.daemon = True
    sp.start()
    while True:
        # look for incoming  request
        if not output_queue.empty():
            data = output_queue.get()
            handle_serial_packet(data)
    try:
        ani = SubplotAnimation(Database)
        # ani.save('test_sub.mp4')
        plt.show()
    except JSONDecodeError as error:
        print('%s is not a valid JSON file. Parsing failed at line %s and column %s. Exiting...',
              config, error.lineno, error.colno)
        sys.exit(1)
    except KeyboardInterrupt:
        print('Received SIGINT signal. Shutting down %s...', command)
        server.stop()
        sys.exit(0)
    except PermissionError as error:
        print(
            'Can\'t read file %s. Make sure you have read permissions. Exiting...', error.filename)
        sys.exit(1)
