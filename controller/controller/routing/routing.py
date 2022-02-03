""" This routing class initializes and, at this time, in a fix period
it runs the given routing algorithm. It uses the network config class
to reconfigure sensor nodes path. """

# from controller.routing.dijkstra.dijkstra import Graph

import re
import time
import threading
import pandas as pd
from controller.routing.check_connected_graph import Connected_graph
# from controller.routing.dijkstra.dijkstra import Vertex
from controller.database.database import Database
# from controller.routing.check_connected_graph import add_edge, is_connected, initialize
from controller.routing.dijkstra.dijkstra import Dijkstra
from controller.routing.graph import Graph, Vertex
from controller.routing.routes import Routes


class Routing(Routes):
    def __init__(self, config):
        print("Initializing routing with Graph")
        super().__init__()
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
            df = pd.DataFrame(list(Database.find("links", {})))
            """ We first need to check whether the given graph is connected or not """
            g = Graph()
            # Add vertices
            v = self.vertex()
            for vertex in v:
                print('vertex')
                print(str(int(float(vertex))))
                g.add_node(Vertex(str(int(float(vertex)))))
            # Add edges
            for index, row in df.iterrows():
                print("adding edge ", str(int(float(row["scr"]))), "-", str(int(
                    float(row["dst"]))), " RSSI ", int(-1*row['rssi']))
                g.add_edge(str(int(float(row["scr"]))), str(int(
                    float(row["dst"]))), int(-1*row['rssi']))
            # Function call
            connected_graph = Connected_graph(g, "1")
            print("is a connected graph?")
            if (connected_graph.run()):
                print("Yes")
                # Now that we are sure the graph is connected, let's run the algorithm
                if(self.config.routing.protocol == "dijkstra"):
                    print("start dijkstra algorithm")
                    # Should we clear all routes before saving any route?
                    # This may be done because some routes may no longer exist
                    self.clear_routes()
                    # Execute the algorithm from source to all nodes
                    for vertex in v:
                        alg = Dijkstra(g, "1", str(int(float(vertex))))
                        path, path_lenght = alg.execution()
                        print(" -> ".join(path))
                        print(f"Length of the path: {path_lenght}")
                        # Iterate over the path and added to the Routes object
                        self.set_routes(path)
                    print("set routes done")
                    self.print_routes()
                    print("routes save to db")
                    self.save_routes_db()
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

    def vertex(self):
        # get the vertecis of the db
        print("Getting the vertices")

        db = Database.find_one("links", {})
        if(db is None):
            print('no entries yet, alg. computing aborting')
            return 0
        else:
            df = pd.DataFrame(list(Database.find("links", {})))
            # Now we want to count the number of element
            values = pd.unique(df[['scr', 'dst']].values.ravel('K'))
            return values

    def set_routes(self, path):
        if(len(path) <= 2):
            return
        # We set the route from the controller to nodes
        for i in range(len(path)-1):
            node = path[i]
            neigbour = path[i+1]
            # Check if we can form a subset
            if((len(path)-2-i) < 1):
                return
            subset = path[-(len(path)-2-i):]
            for j in range(len(subset)):
                # Set the route for the selected node
                # print("adding path ",
                #       path[i], "-", subset[j], "via", neigbour)
                # we set a new route
                self.add_route(node, subset[j], neigbour)
