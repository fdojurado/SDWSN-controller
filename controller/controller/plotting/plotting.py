from ast import Not
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.animation as animation
from controller.forwarding_table.forwarding_table import FWD_TABLE
import networkx as nx
from controller.database.database import Database
import pandas as pd
import multiprocessing as mp
import pymongo


class SubplotAnimation(mp.Process):
    def __init__(self):
        mp.Process.__init__(self)

    def load_data_latest_data(self, collection, source, target, attribute):
        # pymongo.Descending is not necessary here, we may delete it
        db = Database.find_one(collection, {}, [('time', pymongo.DESCENDING)])
        Graph = nx.Graph()
        if(db is None):
            return Graph
        pipeline = [
            {"$sort": {"time": -1}},
            {"$limit": 1},
            {"$unwind": "$routes"},
            {
                '$project': {
                    "_id": 0,
                    'scr': '$routes.scr',
                    'dst': '$routes.dst',
                    'via': '$routes.via'
                }
            }
        ]
        # Make empty dataframe
        df = pd.DataFrame()
        # load last routes in the collection
        for doc in Database.aggregate(collection, pipeline):
            df_doc = pd.DataFrame(doc, index=[0])
            df = pd.concat([df, df_doc], ignore_index=True)
        # Now, we only plot routes that are already acked (deployed)
        list_index = []
        for index, route in df.iterrows():
            db = FWD_TABLE.fwd_get_item(
                route["scr"], route["dst"], route["via"])
            if (db is not None):
                if(db["deployed"] == 0):
                    list_index.append(index)
            else:
                list_index.append(index)
        df = df.drop(index=list_index)
        Graph = nx.from_pandas_edgelist(
            df, source=source, target=target, edge_attr=attribute)
        return Graph

    def load_data(self, collection, source, target, attribute):
        db = Database.find_one(collection, {}, None)
        Graph = nx.Graph()
        if(db is None):
            return Graph
        df = pd.DataFrame(list(Database.find(collection, {})))
        Graph = nx.from_pandas_edgelist(
            df, source=source, target=target, edge_attr=attribute)
        return Graph

    def animate(self, framedata):
        self.G.clear()
        # See if G has changed
        self.G = self.load_data("links", 'scr', 'dst', 'rssi')
        if(nx.is_empty(self.G) == False):
            equal_graphs = nx.is_isomorphic(
                self.prev_G, self.G, edge_match=lambda x, y: x['rssi'] == y['rssi'])  # match weights
            # We only want to redraw the network if this has changed from the previous setup
            if(equal_graphs == False):
                self.ax1.clear()
                self.ax1.set_title('Network links')
                self.prev_G.clear()
                self.prev_G = self.G.copy()
                pos = nx.spring_layout(self.prev_G)  # positions for all nodes
                nx.draw(self.prev_G, pos, with_labels=True, ax=self.ax1)
                labels = nx.get_edge_attributes(self.prev_G, 'rssi')
                nx.draw_networkx_edge_labels(
                    self.prev_G, pos, edge_labels=labels, ax=self.ax1)
        # Now let's redraw the network for the current deployed routes
        # See if G has changed
        self.G = self.load_data_latest_data(
            "historical-routes", 'scr', 'via', None)
        if(nx.is_empty(self.G) == False):
            equal_graphs = nx.is_isomorphic(
                self.prev_routes_G, self.G, edge_match=lambda x, y: x == y)  # match weights
            # We only want to redraw the network if this has changed from the previous setup
            if(equal_graphs == False):
                self.ax2.clear()
                self.ax2.set_title('Current routing')
                self.prev_routes_G.clear()
                self.prev_routes_G = self.G.copy()
                # positions for all nodes
                pos = nx.spring_layout(self.prev_routes_G)
                nx.draw(self.prev_routes_G, pos, with_labels=True, ax=self.ax2)

    def run(self):
        fig = plt.figure()
        self.ax1 = fig.add_subplot(2, 1, 1)
        self.ax1.set_title('Network links')
        self.ax2 = fig.add_subplot(2, 1, 2)
        self.ax2.set_title('Current routing')
        # Or equivalently,  "plt.tight_layout()"
        fig.tight_layout(pad=3.0)

        self.prev_G = nx.Graph()
        self.prev_routes_G = nx.Graph()
        self.G = nx.Graph()

        self.ani = animation.FuncAnimation(
            fig, self.animate, interval=50)
        plt.show()
