""" This routing class initializes and, at this time, in a fix period
it runs the given routing algorithm. It uses the network config class
to reconfigure sensor nodes path. """

# from controller.routing.dijkstra.dijkstra import Graph

from inspect import Attribute
import multiprocessing as mp
from operator import attrgetter
from controller.routing.routes import Routes
from controller.database.database import Database
import networkx as nx
import pandas as pd


def handle_routing(routes):
    routes.save_historical_routes_db()
    routes.save_routes_db()


def load_data(collection, source, target, attribute):
    db = Database.find_one(collection, {})
    Graph = nx.Graph()
    if(db is None):
        return Graph
    df = pd.DataFrame(list(Database.find(collection, {})))
    Graph = nx.from_pandas_edgelist(
        df, source=source, target=target, edge_attr=attribute)
    return Graph


class Routing(mp.Process):
    def __init__(self, config, verbose, alg, input_queue, output_queue):
        mp.Process.__init__(self)
        self.input_queue = input_queue
        self.alg = alg
        self.output_queue = output_queue
        self.interval = int(config.routing.time)
        self.verbose = verbose
        self.routes = Routes()

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
                        match self.alg:
                            case "dijkstra":
                                print("running dijkstra")
                                self.dijkstra(G)
                            case "mst":
                                print("running MST")
                            case _:
                                print("running default alg.")

    def dijkstra(self, G):
        # We want to compute the SP from controller to all nodes
        length, path = nx.single_source_dijkstra(G, "1.0", None, None, "rssi")
        # Now, we want to det this routes
        self.set_routes(path)
        self.routes.print_routes()
        # Let's put the routes in the queue
        self.output_queue.put(self.routes)

    def set_routes(self, path):
        """ Save routes in the 'src'-'dst' 'via' format.
        Return: the connected graph of the given routing algo. """
        for u, p in path.items():
            if(u != '1.0'):
                if(len(p) > 2):
                    # We set the route from the controller to nodes
                    for i in range(len(p)-1):
                        node = p[i]
                        neigbour = p[i+1]
                        # Check if we can form a subset
                        if(not (len(p)-2-i) < 1):
                            subset = p[-(len(p)-2-i):]
                            for j in range(len(subset)):
                                self.routes.add_route(
                                    node, subset[j], neigbour)
                    # Now we add the routes from node to controller
                    # Keep in mind that we only need the neighbour to controller.
                    # We dont need to know the routes to every node in the path to the controller.
                    reverse = p[::-1]
                    node = reverse[0]
                    neigbour = reverse[1]
                    self.routes.add_route(node, "1.0", neigbour)
