""" This routing class initializes and, at this time, in a fix period
it runs the given routing algorithm. It uses the network config class
to reconfigure sensor nodes path. """

# from controller.routing.dijkstra.dijkstra import Graph

from enum import unique
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
        self.run()
#        super(Graph, self).__init__(name, *args, **kwargs)

    def run(self):
        self.compute_routing()
        # Check whether routes has changed since last run
        routes_no_found = self.check_routes_changed()
        if(not routes_no_found.empty):
            print("routes not found")
            print(routes_no_found)
            # Here, we assume that other routes have been previously deployed/reconfigured.
            self.compute_new_routes(routes_no_found)
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
        # Dataframe to store routes not found
        no_found_routes = pd.DataFrame(columns=['src', 'dst', 'via'])
        # Get the data of the last routes
        # Load the routes db in df
        db = Database.find_one("historical-routes", {})
        if(db is None):
            return no_found_routes
        df = pd.DataFrame(list(Database.find("historical-routes", {})))
        # Sort ascending the dataframe based on the time entry
        df = df.sort_values(by=['time'], ascending=False)
        if(len(df) <= 1):
            return no_found_routes
        df_prev = df.iloc[1]
        df_prev_routes = pd.DataFrame(df_prev['routes'])
        print("printing prev routes")
        print(df_prev_routes.to_string())
        print("printing current routes")
        print(self.routes.to_string())
        # Now, we need to compare the current routes with df_prev_routes
        for index, current_route in self.routes.iterrows():
            if not (((current_route['src'] == df_prev_routes['src']) & (current_route['dst'] == df_prev_routes['dst']) & (current_route['via'] == df_prev_routes['via'])).any() |
                    ((current_route['src'] == df_prev_routes['dst']) & (current_route['dst'] == df_prev_routes['src']) & (current_route['via'] == df_prev_routes['via'])).any()):
                current_route = pd.DataFrame([current_route])
                no_found_routes = pd.concat(
                    [no_found_routes, current_route], ignore_index=True)  # adding a row
        return no_found_routes

    def compute_new_routes(self, routes):
        """ Here, we compute new routes per node and trigger send_nc """
        print("computing new routes")
        # We first want to filter routes per node at both source and destination
        unique = pd.unique(routes[['src', 'dst']].values.ravel('K'))
        # Let's get the routes for each unique node
        for node in unique:
            df = routes[routes['src'] == node]
            print("routes for node ", node)
            print(df)

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
