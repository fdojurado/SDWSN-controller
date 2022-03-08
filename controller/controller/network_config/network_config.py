from controller.routing.routing import *
from controller.database.database import Database
from controller.network_config.queue import Queue
from controller.serial.serial_packet_dissector import *
from controller.packet.packet import SerialPacket, ControlPacket, NC_RoutingPacket
import multiprocessing as mp
import networkx as nx
import pandas as pd
import time
# Generate random number for ack
from random import randrange


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
        payload_len = df.shape[0]*4
        # Build packet data
        data_packet = NC_RoutingPacket(df)
        dataPacked = data_packet.pack()
        print(repr(data_packet))
        print(dataPacked)
        # Build control packet
        cp_pkt = ControlPacket(
            dataPacked, type=sdn_protocols.SDN_PROTO_NC, len=payload_len, rank=randrange(65535))
        cpPackedData = cp_pkt.pack()
        print(repr(cp_pkt))
        print(cpPackedData)
        # Build sdn IP packet
        vahl = 0x2a  # 0x2a: version 2, header length 10
        # length of the entire packet
        length = payload_len+CP_PKT_HEADER_SIZE+IP_PKT_HEADER_SIZE
        ttl = 0x40  # 0x40: Time to live
        proto = sdn_protocols.SDN_PROTO_CP  # NC packet
        scr = 0x0101  # Controller is sending
        dest = int(float(node))
        sdn_ip_pkt = SDN_IP_Packet(cpPackedData,
                                   vahl=vahl, len=length, ttl=ttl, proto=proto, scr=scr, dest=dest)
        sdn_ip_packed = sdn_ip_pkt.pack()
        print(repr(sdn_ip_pkt))
        # Control packet as payload of the serial packet
        pkt = SerialPacket(sdn_ip_packed, addr0=0, addr1=0,
                           message_type=2, payload_len=length,
                           reserved0=0, reserved1=0)
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
                    # print("Sending NC packet to node ", node)
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
