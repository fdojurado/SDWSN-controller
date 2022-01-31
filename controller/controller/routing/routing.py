""" This routing class initializes and, at this time, in a fix period
it runs the given routing algorithm. It uses the network config class
to reconfigure sensor nodes path. """

# from controller.routing.dijkstra.dijkstra import Graph

import time
import threading
import pandas as pd
from controller.database.database import Database
from controller.routing.check_connected_graph import add_edge, is_connected


class Routing():
    def __init__(self, config):
        print("Initializing routing with Graph")
        self.config = config
        print(self.config.routing.time)
        self.compute_routing()
#        super(Graph, self).__init__(name, *args, **kwargs)

    def compute_routing(self):
        print("Computing routing algorithm")
        """ We need to read the forwarding table for every node in the database """
        N = self.num_nodes()
        print("number of sensor nodes")
        print(N)
        if(N > 0):
            """ We first need to check whether the given graph is connected or not """
            # add every edge in the links db
            df = pd.DataFrame(list(Database.find("links", {})))
            for index, row in df.iterrows():
                print("adding edge ", row["scr"], "-", row["dst"])
                add_edge(int(float(row["scr"])), int(float(row["dst"])))
            # Function call
            print("is a connected graph?")
            if (is_connected(N)):
                print("Yes")
            else:
                print("No")
        # print(time.ctime())
        threading.Timer(int(self.config.routing.time),
                        self.compute_routing).start()

    """ This function returns the number of sensor nodes in the network """

    def num_nodes(self):
        # Let's check firs if the collection exists
        db = Database.find_one("links", {})
        if(db is None):
            print('no entries yet, alg. computing aborting')
            return 0
        else:
            df = pd.DataFrame(list(Database.find("links", {})))
            print("df")
            print(df)
            # Now we want to count the number of element
            values = pd.unique(df[['scr', 'dst']].values.ravel('K'))
            return len(values)
