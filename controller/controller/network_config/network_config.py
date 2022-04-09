from logging import exception
from controller.forwarding_table.forwarding_table import FWD_TABLE
from controller.routing.routing import *
from controller.database.database import Database
from controller.network_config.queue import Queue
from controller.serial.serial_packet_dissector import *
from controller.packet.packet import SerialPacket, ControlPacket, NC_RoutingPacket
import multiprocessing as mp
import networkx as nx
import pandas as pd
import queue  # or Queue in Python 2
# Generate random number for ack
from random import randrange


""" TODO: Set the maximum routes per node (e.g., 10). 
Remove old routes with the new ones"""


def routes_to_deploy(node, routes):
    """ Remove already deployed routes """
    for index, route in routes.iterrows():
        query = {"$and": [
            {"_id": node},
            {"routes.scr": route["scr"]},
            {"routes.dst": route["dst"]},
            {"routes.via": route["via"]},
        ]}
        db = Database.find_one("nodes", query, None)
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
    df, G = FWD_TABLE.fwd_get_graph('scr', 'via', None, 0)
    length, path = nx.single_source_dijkstra(G, "1.0")
    node_list = []
    for u, p in path.items():
        node_list.extend([str(u)])
    return node_list


class NetworkConfig(mp.Process):
    def __init__(self, verbose, input_queue, output_queue, serial_input_queue, ack_queue):
        mp.Process.__init__(self)
        self.G = nx.Graph()
        self.running = False
        self.verbose = verbose
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.serial_input_queue = serial_input_queue
        self.ack_queue = ack_queue
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
            dataPacked, type=sdn_protocols.SDN_PROTO_NC, len=payload_len, rank=randrange(65535), energy=0xffff)
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
        pkt = SerialPacket(sdn_ip_packed, addr=0,
                           message_type=2, payload_len=length,
                           reserved0=0, reserved1=0)
        packedData = pkt.pack()
        print(repr(pkt))
        return cp_pkt, sdn_ip_pkt, packedData

    def read_routes(self, node):
        df = FWD_TABLE.fwd_get_table()
        df = df[df['scr'] == node]
        if(df.empty):
            return df
        df = df[(df['deployed'] == 0)]
        return df

    def set_route_flag(self, node, df):
        print("setting routes flag")
        for index, route in df.iterrows():
            FWD_TABLE.fwd_set_deployed_flag(
                node, route["dst"], route["via"], 1)

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
                    print("routes to deploy for node ", node)
                    print(df)
                    # build the packet
                    cp_pkt, sdn_ip_pkt, packetData = self.build_packet(
                        node, df)
                    # print("Sending NC packet to node ", node)
                    # set retransmission
                    rtx = 0
                    # Send NC packet
                    self.serial_input_queue.put(packetData)
                    while True:
                        try:
                            ack_pkt = self.ack_queue.get(block=True, timeout=7)
                            if ((ack_pkt.ack == cp_pkt.rank+1) and (ack_pkt.addrStr == node)):
                                print("correct ACK received from ",
                                      ack_pkt.addrStr)
                                # set the routes deployed flag
                                self.set_route_flag(node, df)
                                break
                        except queue.Empty:
                            print("ACK not received from ", node, " rtx ", rtx)
                            # We stop sending the current NC packet if
                            # we reached the max RTX or we received ACK
                            if(rtx >= 7):
                                print("ACK never received from ",
                                      node, " rtx ", rtx)
                                break
                            # We resend the packet if retransmission < 7
                            rtx = rtx + 1
                            self.serial_input_queue.put(packetData)
