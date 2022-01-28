""" This routing class initializes and, at this time, in a fix period
it runs the given routing algorithm. It uses the network config class
to reconfigure sensor nodes path. """

# from controller.routing.dijkstra.dijkstra import Graph

import time, threading

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
        
        """ We first need to check whether the given graph is connected or not """
        # print(time.ctime())
        threading.Timer(int(self.config.routing.time), self.compute_routing).start()
