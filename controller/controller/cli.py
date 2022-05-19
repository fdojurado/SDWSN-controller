# import config
# from controller.serial import SerialBus
# from controller.mqtt_client.mqtt_client import sdwsn_mqtt_client
from hashlib import new
from controller.network_config.network_config import *
from controller.routing.routing import *
from controller.config.serial import SerialConfig
from controller.serial.serial_packet_dissector import *
from controller.plotting.plotting import SubplotAnimation
from controller.mqtt.mqtt import MQTTClient
# from controller.routing.routing import Routing
from controller.serial.serial import SerialBus
from controller.database.database import Database
from controller.config import ServerConfig, DEFAULT_CONFIG
from controller.centralised_scheduler.scheduler import Scheduler
from controller.deep_reinforcement_learning.sdwsn_rl import SDWSN_RL
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
from controller import globals
# device topics
serial_topic = "controller/serial"  # publishing topic

SERVER = {'serial-controller': SerialBus}

""" Initialise database """
Database.initialise()


def main(command, verbose, version, config, plot, mqtt_client, daemon, rl=None, fit=None):
    """The main function run by the CLI command.

    Args:
        command (str): The command to run.
        verbose (bool): Use verbose output if True.
        plot    (bool): Show the plots.
        mqtt    (bool): Run the MQTT client
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
    """ Initialize the global variables """
    globals.globals_initialize()
    """ Define Queues """
    # TSCH scheduler Queues
    scheduler_input_queue = mp.Queue()
    scheduler_output_queue = mp.Queue()
    # Serial Queues
    serial_input_queue = mp.Queue()
    serial_output_queue = mp.Queue()
    # Routing Queues
    routing_input_queue = mp.Queue()
    routing_output_queue = mp.Queue()
    routing_alg_queue = mp.Queue()
    # NC Queues
    nc_input_queue = mp.Queue()
    nc_output_queue = mp.Queue()
    # Queue for ack packets
    ack_queue = mp.Queue()
    """ Start the routing interface in background (as a daemon) """
    # rp stands for routing process
    # We need to consider that the computation of the new routing alg.
    # can be change at run time
    if rl:
        rp = SDWSN_RL(ServerConfig.from_json_file(config), verbose,
                      routing_input_queue, routing_output_queue, nc_input_queue)
    else:
        rp = Routing(ServerConfig.from_json_file(config), verbose, "dijkstra",
                     routing_input_queue, routing_output_queue, routing_alg_queue)
    """ Start the NC interface in background (as a daemon) """
    # nc stands for network configuration
    nc = NetworkConfig(verbose, nc_input_queue,
                       nc_output_queue, serial_input_queue, ack_queue)
    """ Start the serial interface in background (as a daemon) """
    sp = SerialBus(ServerConfig.from_json_file(config, fit),
                   verbose, serial_input_queue, serial_output_queue)
    """ Start the centralized scheduler in background (as a daemon) """
    sc = Scheduler(ServerConfig.from_json_file(config),
                   verbose, scheduler_input_queue, scheduler_output_queue, nc_input_queue)
    """ Let's start the plotting (animation) in background (as a daemon) """
    if plot:
        ntwk_plot = SubplotAnimation()
    """ Let's create the MQTT client """
    if mqtt_client:
        mqtt = MQTTClient(ServerConfig.from_json_file(
            config), verbose, routing_alg_queue)
        mqtt.run()
    """ Let's start all processes """
    sp.daemon = True
    sp.start()
    rp.daemon = True
    rp.start()
    nc.daemon = True
    nc.start()
    sc.daemon = True
    sc.start()
    if plot:
        ntwk_plot.daemon = True
        ntwk_plot.start()
    interval = ServerConfig.from_json_file(config).routing.time
    # timeout = time.time()+int(120.0)
    while True:
        # look for incoming request from the serial interface
        if not serial_output_queue.empty():
            data = serial_output_queue.get()
            handle_serial_packet(data, ack_queue)
        # Run the routing protocol?
        if globals.num_packets_period > 50:
            G = load_wsn_links("rssi")
            routing_input_queue.put(G)
            globals.num_packets_period = 0
        # if(time.time() > timeout):
        #     # put a job
        #     G = load_wsn_links("rssi")
        #     routing_input_queue.put(G)
        #     timeout = time.time() + int(90)
        # look for incoming request from routing
        if not routing_output_queue.empty():
            path, routes_json, routes_matrix = routing_output_queue.get()
            # Set routes matrix to the global scope
            globals.routes_matrix = routes_matrix
            # Compute Schedule Advertisement (SA) packet
            scheduler_input_queue.put(path)
        # look for incoming request from scheduler
        if not scheduler_output_queue.empty():
            schedule_job, link_schedules_matrices = scheduler_output_queue.get()
            # Set link_schedules_matrices to the global scope
            globals.link_schedules_matrices = link_schedules_matrices
            # Send the SA packet
            nc_input_queue.put(schedule_job)
            # We now send Routes Advertisement (RA) packet
            nc_input_queue.put(routes_json)
            # reset the elapse time of the current RA and SA configuration
            globals.elapse_time = datetime.now().timestamp() * 1000.0
            # Trigger save features, so the coming data gets label correctly
            save_features()
        sleep(0.1)
