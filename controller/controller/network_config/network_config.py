import re
from controller.serial.serial import SerialBus
from controller.network_config.queue import Queue
import networkx as nx
import pandas as pd
import threading
import time


class NetworkConfig(object):

    def __init__(self):
        print('init netconfig')
        self.G = nx.Graph()
        self.NC_rt_table_queue = Queue(None)  # Queue for NC packets
        self.NC_ACK = Queue(None)  # Queue for ACKs

    def add_edge_nc(self, u, v):
        print("NC: adding path ", u, "-", v)
        self.G.add_edge(u, v)

    def clear_graph(self):
        self.G.clear()

    def print_edges_nc(self):
        print("printing edges")
        print([e for e in self.G.edges])

    def empty_graph(self):
        return nx.is_empty(self.G)

    def dfs_tree_nc(self):
        print("building dfs tree from controller")
        return nx.dfs_tree(self.G, "1").edges()

    def bfs_tree_nc(self):
        print("building bfs tree from controller")
        return nx.bfs_tree(self.G, "1").edges()

    def send_nc(self, node, rtx):
        print('Sending NC packet ', node, ' rtx ', rtx)

    def process_nc(self):
        print('Processing NC packet')

    def ack_nc(self):
        print('Processing NC ack')

    def clear_routes_nc(self):
        self.routes.drop(self.routes.index, inplace=True)


class SendNC:
    def __init__(self, NetworkConfig, run):
        self.NC = NetworkConfig
        self.thread_run = threading.Event()
        self.thread_ack = threading.Event()

    def run(self):
        while True:
            self.thread_run.wait()
            print("starting NC thread")
            self.NC.NC_rt_table_queue.print_queue()
            # We loop until the Queue is empty
            while self.NC.NC_rt_table_queue._queue:
                x = self.NC.NC_rt_table_queue.dequeue()
                print("Sending NC packet to node ", x)
                # set retransmission
                rtx = 0
                # Send NC packet
                self.NC.send_nc(x, rtx)
                # We first set the timeout
                timeout = time.time() + 7   # 7 seconds from now
                while True:
                    # We resend the packet if timeout and retransmission < 7
                    if((time.time() > timeout) and (rtx < 7)):
                        # Send NC packet
                        rtx = rtx + 1
                        self.NC.send_nc(x, rtx)
                        timeout = time.time() + 7   # 7 seconds from now
                    # We stop sending the current NC packet if
                    # we reached the max RTX or we received ACK
                    if(rtx >= 7):
                        break
                    time.sleep(1)
                    # If we received the correct ACK
                    # if(True):
                    #     break
            self.thread_run.clear()
