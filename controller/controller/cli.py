# import config
# from controller.serial import SerialBus
# from controller.mqtt_client.mqtt_client import sdwsn_mqtt_client
from hashlib import new
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

from daemon import DaemonContext
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


def serial_interface(command, config, verbose):
    server_class = SERVER[command]
    print('Creating %s object...', server_class.__name__)
    server = server_class(ServerConfig.from_json_file(config), verbose)
    print("server")
    print(server)
    server.start()


def main(command, verbose, version, config, daemon):
    """The main function run by the CLI command.

    Args:
        command (str): The command to run.
        verbose (bool): Use verbose output if True.
        version (bool): Print version information and exit if True.
        config (str): Configuration file.
        daemon (bool): Run as a daemon if True.
    """
    print('hello')
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
    # root = tk.Tk()
    # MainApplication(root).pack(side="top", fill="both", expand=True)
    # root = Tk()
    """ Initialise database """
    Database.initialise()
    """ Initialise routing """
    Routing(ServerConfig.from_json_file(config))

    try:

        # logger = get_logger(command, verbose, daemon)
        # print('%s %s', command, VERSION)

        # Start the program as a daemon.
        if daemon:
            print('Starting daemon...')
            context = DaemonContext(files_preserve=[logger.handlers[0].socket])
            context.signal_map = {signal.SIGQUIT: exit_process,
                                  signal.SIGTERM: exit_process}
            context.open()

        if not config:
            print('Using default configuration file.')
            config = DEFAULT_CONFIG

        p = mp.Process(target=serial_interface, args=[
            command, config, verbose])
        p.start()
        # call the animator.  blit=True means only re-draw the parts that have changed.
        ani = SubplotAnimation(Database)
        # ani.save('test_sub.mp4')
        plt.show()
        # anim = animation.FuncAnimation(
        #     fig, animate, fargs=(Database, Routing,), interval=2000)
        # plt.show()

    # except ConfigurationFileNotFoundError as error:
    #     print(
    #         'Configuration file %s not found. Exiting...', error.filename)
    #     sys.exit(1)
    except JSONDecodeError as error:
        print('%s is not a valid JSON file. Parsing failed at line %s and column %s. Exiting...',
              config, error.lineno, error.colno)
        sys.exit(1)
    except KeyboardInterrupt:
        print('Received SIGINT signal. Shutting down %s...', command)
        server.stop()
        sys.exit(0)
    # except NoDefaultAudioDeviceError as error:
    #     print('No default audio %s device available. Exiting...',
    #                     error.inout)
    #     sys.exit(1)
    except PermissionError as error:
        print(
            'Can\'t read file %s. Make sure you have read permissions. Exiting...', error.filename)
        sys.exit(1)

    # """ Initialise MQTT """
    # if not config:
    #     logger.debug('Using default configuration file.')
    #     config = DEFAULT_CONFIG
    # server = server_class(ServerConfig.from_json_file(config))
    # """ Initialise Serial Interface """
    # serial = SerialBus('localhost', 60001)
    # if serial.connect() == 1:
    #     print('connection succesful')
    #     # controller.show_frame(MainPage)
    # else:
    #     print('connection unsuccesful')

    # """ Initialise MQTT Interface """
    # mqtt_client = sdwsn_mqtt_client(
    #     'localhost', 1883, 'SDWSN controller', 'sS0J03qjGyn0K5z8ubzy')

    # rc = mqtt_client.run()

    # print("rc: "+str(rc))
    # send_msg = {
    #     'temperature': 32,
    #     'humidity': 25
    # }
    # mqtt_client.publish(serial_topic, json.dumps(send_msg))
    # a = Database.insert("example", user)
    # print(a)
    # Database.print_documents("nodes")
    # Database.list_collections()
    # """ Initialise GUI """
    # app = SDNcontrollerapp()
    # app.geometry("1280x720")
    # ani = animation.FuncAnimation(f, animate, interval=5000)
    # app.mainloop()
    # while True:
    #     time.sleep(1)
