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


routes_matrix = np.array([])


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
        if(u != 1):
            if(len(p) >= 2):
                # We set the route from the controller to nodes
                # for i in range(len(p)-1):
                #     node = p[i]
                #     neighbor = p[i+1]
                #     # Check if we can form a subset
                #     if(not (len(p)-2-i) < 1):
                #         subset = p[-(len(p)-2-i):]
                #         for j in range(len(subset)):
                #             rts.add_route(
                #                 node, subset[j], neighbor)
                # Now we add the routes from node to controller
                # Keep in mind that we only need the neighbor to controller.
                # We don't need to know the routes to every node in the path to the controller.
                # reverse = p[::-1]
                node = p[0]
                neighbor = p[1]
                rts.add_route(str(node)+".0", "1.1", str(neighbor)+".0")
    return rts


def save_routes(rts):
    rts.save_historical_routes_db()
    rts.save_routes_db()


def load_wsn_links(type):
    G = nx.DiGraph()
    match type:
        case "rssi":
            matrix = get_nbr_rssi_matrix()*-1
        case "etx":
            matrix = get_nbr_etx_matrix()
    if(matrix.size <= 1):
        return G
    G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
    print("matrix")
    print(matrix)
    print(G.edges.data())
    G.remove_nodes_from(list(nx.isolates(G)))
    print(G.nodes)
    return G


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
                    # for node1, node2, data in G.edges(data=True):
                    #     nx.set_edge_attributes(
                    #         G, {(node1, node2): {'rssi': data['rssi']*-1}})
                    # if(nx.is_connected(G)): # Not implemented for direct graph
                    # Now that we are sure it is a connected graph,
                    # we now run the selected routing algorithm
                    if(G.has_node(1)):  # Maybe use "1.0" instead
                        # Check if the routing algorithm has changed
                        if not self.routing_alg_queue.empty():
                            self.alg = self.routing_alg_queue.get()
                            print("algorithm changed to ", self.alg)
                        match self.alg:
                            case "dijkstra":
                                print("running dijkstra")
                                path = self.dijkstra(G)
                            case "mst":
                                print("running MST")
                                path = self.mst(G)
                            case _:
                                print("running default alg.")
                        # Let's put the path in matrix format
                        self.build_routes_matrix(path)
                        self.output_queue.put(path)

    def dijkstra(self, G):
        # We want to compute the SP from all nodes to the controller
        path = {}
        for node in list(G.nodes):
            if node != 1 and node != 0:
                print("sp from node "+str(node))
                try:
                    node_path = nx.dijkstra_path(G, node, 1, weight='weight')
                    print("dijkstra path")
                    print(node_path)
                    path[node] = node_path
                except nx.NetworkXNoPath:
                    print("path not found")
        print("total path")
        print(path)
        # length, path = nx.single_source_dijkstra(G, 1, None, None, "weight")
        # print("dijkstra path")
        # print(path)
        # Let's put the path in the queue
        return path

    def mst(self, G):
        # We want to compute the MST of the current connected network
        # We call the edges "path"
        mst = nx.minimum_spanning_tree(G, algorithm="kruskal", weight="weight")
        return self.dijkstra(mst)

    def build_routes_matrix(self, path):
        global routes_matrix
        # Get last index of sensor
        N = get_last_index_wsn()+1
        routes_matrix = np.zeros(shape=(N, N))
        for u, p in path.items():
            if(len(p) >= 2):
                routes_matrix[p[0]][p[1]] = 1
        print("routing matrix")
        print(routes_matrix)
        # Save in DB
        current_time = datetime.now().timestamp() * 1000.0
        data = {
            "timestamp": current_time,
            "routes": routes_matrix.flatten().tolist()
        }
        Database.insert(ROUTING_PATHS, data)
