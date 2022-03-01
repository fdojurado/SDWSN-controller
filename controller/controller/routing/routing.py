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
    routing_G = nx.Graph()
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
                    dijkstra(G, routing_G, routes)
                    return
                case "mst":
                    print("running MST")
                    return
                case _:
                    print("running default alg.")
                    return


def dijkstra(G, routing_G, routes):
    # We want to compute the SP from controller to all nodes
    for target in list(G.nodes):
        if(target != "1.0"):
            print("shortest path from 1.0 to ", target)
            result = nx.dijkstra_path(G, "1.0", target, "rssi")
            print("result")
            print(result)
            set_routes(G, result, routing_G, routes)
    print("resulting G")
    print(routing_G)
    print("edges of G")
    print(list(routing_G.edges))
    print("attributes of G")
    for node1, node2, data in routing_G.edges(data=True):
        print(node1, "-", node2, " rssi: ", data)
    print("resulting routes")
    routes.print_routes()


def set_routes(G, path, routing_G, routes):
    """ Save routes in the 'src'-'dst' 'via' format.
    Return: the connected graph of the given routing algo. """
    if(len(path) <= 2):
        return
    # We set the route from the controller to nodes
    for i in range(len(path)-1):
        node = path[i]
        neigbour = path[i+1]
        # Save edge source-dest 'weight'
        e = (node, neigbour)
        edge_attribute = G.get_edge_data(*e)
        print("edge_attribute")
        print(edge_attribute)
        routing_G.add_edge(node, neigbour, edge_attribute)
        # Check if we can form a subset
        if(not (len(path)-2-i) < 1):
            subset = path[-(len(path)-2-i):]
            for j in range(len(subset)):
                routes.add_route(node, subset[j], neigbour)
    # Now we add the routes from node to controller
    # Keep in mind that we only need the neighbour to controller.
    # We dont need to know the routes to every node in the path to the controller.
    reverse = path[::-1]
    node = reverse[0]
    neigbour = reverse[1]
    routes.add_route(node, "1.0", neigbour)
