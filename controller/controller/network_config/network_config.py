from controller.routing.routing import *
from controller.database.database import Database
from controller.network_config.queue import Queue
from controller.serial.serial_packet_dissector import *
from controller.packet.packet import SerialControlPacket
from controller import Message
import multiprocessing as mp
import networkx as nx
import pandas as pd
import threading
import time


def routes_to_deploy(node, routes):
    """ Remove already deployed routes """
    for index, route in routes.iterrows():
        query = {"$and": [
            {"_id": node},
            {"routes.scr": route["scr"]},
            {"routes.dst": route["dst"]},
            {"routes.via": route["via"]},
        ]}
        db = Database.find_one("nodes", query)
        print("printing db for route")
        print(route)
        print("printing db for route2")
        print(db)
        if(db is None):
            data = {
                "scr": route["scr"],
                "dst": route["dst"],
                "via": route["via"],
                "deployed": 0
            }
            Database.push_doc("nodes", node, 'routes', data)
        else:
            print("route already exists in deployed")


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
            # Save routes in the "nodes" collection if they don't exist
            routes_to_deploy(node, routes)
        return nodes
        # Now, we process routes for each sensor node


class NetworkConfig(mp.Process):
    def __init__(self, verbose, input_queue, output_queue, serial_input_queue):
        mp.Process.__init__(self)
        self.G = nx.Graph()
        self.running = False
        self.verbose = verbose
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.serial_input_queue = serial_input_queue
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

    def build_packet(self, node, df):
        payload_len = CP_PKT_HEADER_SIZE+df.shape[0]*4
        # Loop in routes
        payload = []
        for index, route in df.iterrows():
            dst = route['dst']
            via = route['via']
            payload.append(int(float(dst)))
            payload.append(int(float(via)))
        print("payload")
        print(payload)
        pkt = SerialControlPacket(payload, addr0=0, addr1=0,
                                  message_type=2, payload_len=payload_len, reserved0=0, reserved1=0)
        packedData = pkt.pack()
        print(repr(pkt))
        return packedData

    def read_routes(self, node):
        query = {"$and": [
                {"_id": node},
                {"routes": {"$exists": True}}
        ]}
        df = pd.DataFrame()
        db = Database.find_one("nodes", query)
        if(db is None):
            return df
        df = pd.DataFrame(db['routes'])
        df = df[(df['deployed'] == 0)]
        return df

    def run(self):
        while True:
            # look for incoming jobs
            if not self.input_queue.empty():
                self.running = True
                node = self.input_queue.get()
                print("there is a new job")
                print(node)
                # read routes from node
                df = self.read_routes(node)
                if(not df.empty):
                    print("routes for node ", node)
                    print(df)
                    # build the packet
                    packetData = self.build_packet(node, df)
                    print("Sending NC packet to node ", node)
                    # set retransmission
                    rtx = 0
                    # Send NC packet
                    self.serial_input_queue.put(packetData)
                    # We first set the timeout
                    timeout = time.time() + 7   # 7 seconds from now
                    while True:
                        # We resend the packet if timeout and retransmission < 7
                        if((time.time() > timeout) and (rtx < 7)):
                            # Send NC packet
                            rtx = rtx + 1
                            self.serial_input_queue.put(packetData)
                            timeout = time.time() + 7   # 7 seconds from now
                        # We stop sending the current NC packet if
                        # we reached the max RTX or we received ACK
                        if(rtx >= 7):
                            break
                        time.sleep(1)
                        # If we received the correct ACK
                        # if(True):
                        #     break
