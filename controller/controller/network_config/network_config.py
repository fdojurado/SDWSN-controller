import re
from controller.serial.serial import SerialBus
import networkx as nx
import pandas as pd


class NetworkConfig(object):

    def __init__(self):
        print('init netconfig')
        self.G = nx.Graph()

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

    def send_nc(self):
        print('Sending NC packet')

    def process_nc(self):
        print('Processing NC packet')

    def ack_nc(self):
        print('Processing NC ack')

    def clear_routes_nc(self):
        self.routes.drop(self.routes.index, inplace=True)