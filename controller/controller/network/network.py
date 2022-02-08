# See this website: http://jakevdp.github.io/blog/2012/08/18/matplotlib-animation-tutorial/

import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt
import threading
from controller.database.database import Database
import pandas as pd
import numpy as np


class Network():
    def __init__(self):
        print("initializing the network visualization tool")
        Database.initialise()
        self.nodes = []
        self.edges = []
        self.G = nx.Graph()
        self.pos = []
        self.df = []

    def position(self):
        self.pos = nx.nx_agraph.graphviz_layout(self.G)

    def get_graph(self):
        return self.G

    def draw_nodes(self):
        self.nodes = nx.draw_networkx_nodes(self.G, self.pos)
        return self.nodes

    def draw_edges(self):
        self.edges = nx.draw_networkx_edges(self.G, self.pos)

    def load_data(self):
        db = Database.find_one("links", {})
        if(db is None):
            # print("no db in links")
            return False
        print("new db in links")
        self.df = pd.DataFrame(list(Database.find("links", {})))
        self.G = nx.from_pandas_edgelist(
            self.df, source='scr', target='dst', edge_attr=True)
        return True

    # def terminate(self):
    #     plt.close('all')

    # def run(self):
    #     print("drawing all links in the network from dataframe")
    #     # Get data from database
    #     db = Database.find_one("links", {})
    #     if(db is None):
    #         print("no db in links")
    #         return
    #     plt.clf()
    #     df = pd.DataFrame(list(Database.find("links", {})))
    #     print("links in visualization")
    #     print(df)
    #     G = nx.from_pandas_edgelist(
    #         df, source='scr', target='dst', edge_attr=True)
    #     print("G")
    #     print(G)
    #     nx.draw_networkx(G)
    #     plt.show()
