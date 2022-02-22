""" This routing class initializes and, at this time, in a fix period
it runs the given routing algorithm. It uses the network config class
to reconfigure sensor nodes path. """

# from controller.routing.dijkstra.dijkstra import Graph

from enum import unique
import re
import time
import threading
import pandas as pd
from controller.network_config.network_config import NetworkConfig
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
        self.nc = NetworkConfig()
        print(self.config.routing.time)
        self.run()
#        super(Graph, self).__init__(name, *args, **kwargs)

    def run(self):
        self.compute_routing()
        # Check whether routes have changed since last run
        self.check_routes_changed()
        # if(not routes_no_found.empty):
        #     print("routes not found")
        #     print(routes_no_found)
        #     # Here, we assume that other routes have been previously deployed/reconfigured.
        #     # Rv: This assumption is not londer valid, we need to check whether routes are
        #     # already deployed in the sensor or not.
        #     self.compute_new_routes(routes_no_found)
        threading.Timer(int(self.config.routing.time),
                        self.run).start()

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
                    self.nc.clear_graph()
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
                    self.save_historical_routes_db()
                    # Here, we want to save the routes into a single object entry.
                    self.save_routes_db()
            else:
                print("No")
        # print(time.ctime())

    def check_routes_changed(self):
        """ Here, we check whether current routes have been already deployed or not """
        # Make sure it is not an empty graph
        if(self.nc.empty_graph() == False):
            self.nc.print_edges_nc()
            tree = self.nc.dfs_tree_nc()
            print("tree")
            print(tree)
            print("list of tree")
            print(list(tree))
            # Lets set the routes for the controller
            self.compute_routes('1')
            # We now loop through the tree
            for node in tree:
                # We get the second element
                target = node[1]
                # we now look for all routes of this node
                # and send the NC packet
                self.compute_routes(target)
        # Loop through the routes
        # for index, route in self.routes.iterrows():
        #     # Here, we first check if the route already exist in sensor node.
        #     db = Database.find_one(
        #         "nodes", {"$and": [
        #             {"_id": route['scr']},
        #             {"dst": route['dst']},
        #             {"via": route['via']}
        #         ]
        #         }
        #     )
        #     if (db is None):
        #         print("none")

    def compute_routes(self, node):
        """ Here, we compute new routes per node and trigger send_nc """
        # column_names = ['node', 'dst', 'via']
        # routes = pd.DataFrame(columns=column_names)
        print("computing new routes for node ", node)
        # We select routes for target node
        df = self.routes[self.routes['scr'] == node]
        print("routes for node ", node)
        print(df.to_string())
        # Now, we want to make sure these routes dont exist
        # in the routing table of the target nodes
        for index, route in df.iterrows():
            addr = route['scr']+'.0'
            dst = route['dst']+'.0'
            via = route['via']+'.0'
            # print("testing route ", addr, "-", dst, " via ", via)
            db = Database.find_one(
                "nodes", {"routes": {"$elemMatch": {"dst": dst, 'via': via}}}
            )
            if (db is None):
                print("route does not exist in routes field of the nodes collection")
                # Add route to sensors routing table db
                data = {
                    'dst': dst,
                    'via': via,
                    'deployed': 0
                }
                node = {
                    '_id': addr,
                    'routes': [
                        data,
                    ]
                }
                if Database.exist("nodes", addr) == 0:
                    print('node does not exist, inserting...')
                    Database.insert("nodes", node)
                else:
                    print('node does exist, pushing...')
                    Database.push_doc("nodes", addr, 'routes', data)

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
            self.nc.add_edge_nc(node, neigbour)
            # Check if we can form a subset
            if(not (len(path)-2-i) < 1):
                subset = path[-(len(path)-2-i):]
                for j in range(len(subset)):
                    # Set the route for the selected node
                    # print("adding path ",
                    #       path[i], "-", subset[j], "via", neigbour)
                    # we set a new route
                    self.add_route(node, subset[j], neigbour)
        # Now we add the routes from node to controller
        # Keep in mind that we only need the neighbour to controller.
        # We dont need to know the routes to every node in the path to the controller.
        reverse = path[::-1]
        print("reverse path")
        print(reverse)
        node = reverse[0]
        neigbour = reverse[1]
        self.add_route(node, "1", neigbour)
        print("exiting set_routes")
