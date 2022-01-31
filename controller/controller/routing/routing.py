""" This routing class initializes and, at this time, in a fix period
it runs the given routing algorithm. It uses the network config class
to reconfigure sensor nodes path. """

# from controller.routing.dijkstra.dijkstra import Graph

import time
import threading
import pandas as pd
from controller.routing.check_connected_graph import Connected_graph
from controller.routing.dijkstra.dijkstra import Vertex
from controller.database.database import Database
# from controller.routing.check_connected_graph import add_edge, is_connected, initialize
from controller.routing.dijkstra.dijkstra import Graph, dijkstra, shortest


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
            connected_graph = Connected_graph()
            # add every edge in the links db
            df = pd.DataFrame(list(Database.find("links", {})))
            for index, row in df.iterrows():
                print("adding edge ", row["scr"], "-", row["dst"])
                connected_graph.add_edge(
                    int(float(row["scr"])), int(float(row["dst"])))
            # Function call
            print("is a connected graph?")
            if (connected_graph.is_connected(N)):
                print("Yes")
                # Now that we are sure the graph is connected, let's run the algorithm
                if(self.config.routing.protocol == "dijkstra"):
                    print("start dijkstra algorithm")
                    g = Graph()
                    # Add vertices
                    v = self.vertex()
                    for vertex in v:
                        print('vertex')
                        print(str(int(float(vertex))))
                        g.add_vertex(str(int(float(vertex))))
                    # Add edges
                    for index, row in df.iterrows():
                        g.add_edge(int(float(row["scr"])), int(
                            float(row["dst"])), int(-1*row['rssi']))
                    print('Graph data:')
                    for v in g:
                        for w in v.get_connections():
                            vid = v.get_id()
                            wid = w.get_id()
                            print('( %s , %s, %3d)'  % ( vid, wid, v.get_weight(w)))
                    dijkstra(g, g.get_vertex('1')) 
                    target = g.get_vertex('3')
                    path = [target.get_id()]
                    shortest(target, path)
                    print('The shortest path : %s' %(path[::-1]))

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
