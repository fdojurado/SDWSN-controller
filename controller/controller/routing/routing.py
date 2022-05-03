""" This routing class initializes and, at this time, in a fix period
it runs the given routing algorithm. It uses the network config class
to reconfigure sensor nodes path. """

# from controller.routing.dijkstra.dijkstra import Graph

from inspect import Attribute
import multiprocessing as mp
from operator import attrgetter
from controller.routing.routes import Routes
from controller.database.database import Database
from controller.serial.serial_packet_dissector import *
import networkx as nx
import pandas as pd
import json
from controller.forwarding_table.forwarding_table import FWD_TABLE
from controller.network_config.network_config import *


def routes_toJSON():
    # Build the routing job in a JSON format to be shared with the NC class
    # Hop limit sets the maximum of hops to bc this message. 255 means all.
    # {
    #   "job_type": "Routing",
    #   "routes":[
    #               {
    #                   "scr": row['scr'],
    #                   "dst": row['dst'],
    #                   "via": row['via']
    #                },
    #               {
    #                   "scr": row['scr'],
    #                   "dst": row['dst'],
    #                   "via": row['via']
    #                }
    #       ],
    #   "hop_limit": "255"
    # }
    json_message_format = '{"job_type": ' + \
        str(job_type.ROUTING)+', "routes":[]}'
    # parsing JSON string:
    json_message = json.loads(json_message_format)
    df = FWD_TABLE.fwd_get_table()
    for index, row in df.iterrows():
        data = {"scr": row['scr'], "dst": row['dst'], "via": row['via']}
        json_message["routes"].append(data)
    # TODO: We need to look for the rank values of all route sources and
    # set the hop limit to the highest rank among the source address.
    json_message["hop_limit"] = 255
    json_dump = json.dumps(json_message, indent=4, sort_keys=True)
    print(json_dump)
    return json_dump


def compute_routes_from_path(path):
    """ Save routes in the 'src'-'dst' 'via' format.
    Return: the connected graph of the given routing algo. """
    rts = Routes()
    for u, p in path.items():
        if(u != '1.0'):
            if(len(p) >= 2):
                # We set the route from the controller to nodes
                # for i in range(len(p)-1):
                #     node = p[i]
                #     neigbour = p[i+1]
                #     # Check if we can form a subset
                #     if(not (len(p)-2-i) < 1):
                #         subset = p[-(len(p)-2-i):]
                #         for j in range(len(subset)):
                #             rts.add_route(
                #                 node, subset[j], neigbour)
                # Now we add the routes from node to controller
                # Keep in mind that we only need the neighbour to controller.
                # We dont need to know the routes to every node in the path to the controller.
                reverse = p[::-1]
                node = reverse[0]
                neigbour = reverse[1]
                rts.add_route(node, "1.1", neigbour)
    return rts


def save_routes(rts):
    rts.save_historical_routes_db()
    rts.save_routes_db()


def load_wsn_links(type):
    match type:
        case "rssi":
            matrix = get_nbr_rssi_matrix()
        case "etx":
            matrix = get_nbr_etx_matrix()
    if(matrix.size <= 1):
        return
    G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
    if(nx.is_empty(G) == False):
        print("matrix")
        print(matrix)
        print(G.edges.data())
    # print("nbr_rssi_matrix.size")
    # print(nbr_rssi_matrix.size)
    # nbr_rssi_matrix
    # db = Database.find_one(collection, {}, None)
    # df = pd.DataFrame()
    # Graph = nx.Graph()
    # if(db is None):
    #     return df, Graph
    # df = pd.DataFrame(list(Database.find(collection, {})))
    # Graph = nx.from_pandas_edgelist(
    #     df, source=source, target=target, edge_attr=attribute)
    # return df, Graph


class Routing(mp.Process):
    def __init__(self, config, verbose, alg, input_queue, output_queue, routing_alg_queue):
        mp.Process.__init__(self)
        self.input_queue = input_queue
        self.alg = alg
        self.output_queue = output_queue
        self.routing_alg_queue = routing_alg_queue
        self.interval = int(config.routing.time)
        self.verbose = verbose

    def set_algorithm(self, alg):
        self.alg = alg

    def run(self):
        # If there is somenthing in the Queue process it
        while(1):
            # look for incoming jobs
            if not self.input_queue.empty():
                G = self.input_queue.get()
                # We first make sure the G is not empty
                if(nx.is_empty(G) == False):
                    for node1, node2, data in G.edges(data=True):
                        nx.set_edge_attributes(
                            G, {(node1, node2): {'rssi': data['rssi']*-1}})
                    if(nx.is_connected(G)):
                        # Now that we are sure it is a connected graph,
                        # we now run the selected routing algorithm
                        if(G.has_node("1.0")):
                            # Check if the routing algorithm has changed
                            if not self.routing_alg_queue.empty():
                                self.alg = self.routing_alg_queue.get()
                                print("algorithm changed to ", self.alg)
                            match self.alg:
                                case "dijkstra":
                                    print("running dijkstra")
                                    self.dijkstra(G)
                                case "mst":
                                    print("running MST")
                                    self.mst(G)
                                case _:
                                    print("running default alg.")

    def dijkstra(self, G):
        # We want to compute the SP from controller to all nodes
        length, path = nx.single_source_dijkstra(G, "1.0", None, None, "rssi")
        print("dijkstra path")
        print(path)
        # Let's put the path in the queue
        self.output_queue.put(path)

    def mst(self, G):
        # We want to compute the MST of the current connected network
        # We call the edges "path"
        mst = nx.minimum_spanning_tree(G, algorithm="kruskal", weight="rssi")
        self.dijkstra(mst)
