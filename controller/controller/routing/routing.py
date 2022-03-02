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


def load_data(collection, source, target, attribute):
    db = Database.find_one(collection, {})
    Graph = nx.Graph()
    if(db is None):
        # print("no db in links")
        return Graph
    df = pd.DataFrame(list(Database.find(collection, {})))
    Graph = nx.from_pandas_edgelist(
        df, source=source, target=target, edge_attr=attribute)
    return Graph


def run_routing(alg):
    # Load data from DB
    G = load_data("links", 'scr', 'dst', 'rssi')
    routes = Routes()
    # We first make sure the G is not empty
    if(nx.is_empty(G) == False):
        print("compute routing started")
        print(G)
        for node1, node2, data in G.edges(data=True):
            nx.set_edge_attributes(
                G, {(node1, node2): {'rssi': data['rssi']*-1}})
        print("printing edges")
        for node1, node2, data in G.edges(data=True):
            print("data")
            print(data)
            print(node1, "-", node2, " :", data['rssi'])

        if(nx.is_connected(G)):
            print("it is a connected graph")
            # Now that we are sure it is a connected graph,
            # we now run the selected routing algorithm
            match alg:
                case "dijkstra":
                    print("running dijkstra")
                    dijkstra(G, routes)
                    return routes
                case "mst":
                    print("running MST")
                    return
                case _:
                    print("running default alg.")
                    return


def dijkstra(G, routes):
    # We want to compute the SP from controller to all nodes
    length, path = nx.single_source_dijkstra(G, "1.0", None, None, "rssi")
    print("path")
    print(path)
    print("length")
    print(length)
    # Now, we want to det this routes
    set_routes(path, routes)
    print("resulting routes")
    routes.print_routes()
    # Let's now save the routes
    routes.save_historical_routes_db()
    routes.save_routes_db()


def set_routes(path, routes):
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
                            routes.add_route(node, subset[j], neigbour)
                # Now we add the routes from node to controller
                # Keep in mind that we only need the neighbour to controller.
                # We dont need to know the routes to every node in the path to the controller.
                reverse = p[::-1]
                node = reverse[0]
                neigbour = reverse[1]
                routes.add_route(node, "1.0", neigbour)
