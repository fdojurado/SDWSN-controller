# import config
# from controller.serial import SerialBus
# from controller.mqtt_client.mqtt_client import sdwsn_mqtt_client
from hashlib import new
from controller.network_config.network_config import *
from controller.routing.routing import *
from controller.serial.serial_packet_dissector import *
from controller.plotting.plotting import SubplotAnimation
# from controller.routing.routing import Routing
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

""" Initialise database """
Database.initialise()


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
    """ Define Queues """
    # Serial Queues
    serial_input_queue = mp.Queue()
    serial_output_queue = mp.Queue()
    # Routing Queues
    routing_input_queue = mp.Queue()
    routing_output_queue = mp.Queue()
    # NC Queues
    nc_input_queue = mp.Queue()
    nc_output_queue = mp.Queue()
    """ Start the routing interface in background (as a daemon) """
    # rp stands for routing process
    # We need to consider that the computation of the new routing alg.
    # can be change at run time
    rp = Routing(ServerConfig.from_json_file(config), verbose, "dijkstra",
                 routing_input_queue, routing_output_queue)
    """ Start the NC interface in background (as a daemon) """
    # nc stands for network configuration
    nc = NetworkConfig(verbose, nc_input_queue, nc_output_queue)
    """ Start the serial interface in background (as a daemon) """
    sp = SerialBus(ServerConfig.from_json_file(config),
                   verbose, serial_input_queue, serial_output_queue)
    """ Let's start all processes """
    sp.daemon = True
    sp.start()
    rp.daemon = True
    rp.start()
    nc.daemon = True
    nc.start()
    interval = ServerConfig.from_json_file(config).routing.time
    timeout = time.time()+int(interval)
    while True:
        # Run the routing protocol?
        if(time.time() > timeout):
            # put a job
            df, G = load_data("links", 'scr', 'dst', 'rssi')
            routing_input_queue.put(G)
            timeout = time.time() + int(interval)
        # look for incoming request from routing
        if not routing_output_queue.empty():
            path = routing_output_queue.get()
            rts = compute_routes_from_path(path)
            save_routes(rts)
            # We now trigger NC
            nodes = compute_routes_nc()
            # Now, we put them in the Queue
            for node in nodes:
             nc_input_queue.put(node)
            # nc_input_queue.put(path)
        # look for incoming request from the serial interface
        if not serial_output_queue.empty():
            data = serial_output_queue.get()
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
