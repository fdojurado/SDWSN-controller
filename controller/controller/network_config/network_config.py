import re
from controller.serial.serial import SerialBus
from controller.routing.routing import *
from controller.database.database import Database
from controller.network_config.queue import Queue
import multiprocessing as mp
import networkx as nx
import pandas as pd
import threading
import time
from networkx.algorithms import tree


def is_deployed(node, route):
    """ Check if route has been already deployed """
    db = Database.find_one("nodes", {"$and": [
        {"_id": node},
        {"routes": {"$exists": True}}
    ]
    }
    )
    if(db is None):
        return route
    # The field exist, we now need to check if the specific route exists
    print("the route field exists for node ", node)
    df = pd.DataFrame(db['routes'])
    print(df)
    return route


def compute_routes_nc():
    df, G = load_data("routes", 'scr', 'via', None)
    if(nx.is_empty(G) == False):
        H = nx.DiGraph()
        H.add_edges_from(G.edges)
        # Get ordered list of nodes to send NC packet
        nodes = list(nx.topological_sort(H))
        for node in nodes:
            print("list of routes for node ", node)
            # Get the list of routes to send
            routes = df[df['scr'] == node]
            print("routes")
            print(routes)
            # Check if these routes have been previously deployed
            new_routes = is_deployed(node, routes)
            print("new routes")
            print(new_routes)
        # Now, we process routes for each sensor node


class NetworkConfig(mp.Process):
    def __init__(self, verbose, input_queue, output_queue):
        mp.Process.__init__(self)
        self.G = nx.Graph()
        self.running = False
        self.verbose = verbose
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.NC_routes = Queue(None)  # Queue for NC packets
        self.NC_ACK = Queue(None)  # Queue for ACKs

    def is_running(self):
        return self.running

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

    def run(self):
        while True:
            # look for incoming jobs
            if not self.input_queue.empty():
                self.running = True
                path = self.input_queue.get()
                # read from routes
                self.read_from_routes(path)
                # Compute the routes for each node
                self.compute_routes(path)
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
