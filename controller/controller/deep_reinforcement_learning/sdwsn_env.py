""" This is the implemantion of the Software-Defined Wireless Sensor Network
environment """
from controller.serial.serial_packet_dissector import *
from controller.routing.routes import Routes
import random
from scipy import rand
import networkx as nx
import gym
from gym import spaces
import numpy as np


class sdwsnEnv(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, num_nodes, max_channel_offsets, slotframe_sizes):
        super(sdwsnEnv, self).__init__()
        self.num_nodes = num_nodes
        self.max_channel_offsets = max_channel_offsets
        self.slotframe_sizes = slotframe_sizes
        self.max_slotframe_size = max(slotframe_sizes)
        # Keep track of the running routes
        self.routes = Routes()
        # We define the number of actions
        # 1) change parent node of a specific node (size: 1 * num_nodes * num_nodes)
        # 2) slotframe size one
        # 3) slotframe size two
        # 4) slotframe size three
        # -- 4) change timeoffset of a specific node (size: 1 * num_nodes)
        # -- 5) change channeloffset of a specific node (size: 1 * num_nodes)
        # 5) add a new RX link of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size )
        # 6) add a new Tx link to parent of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # 7) remove a Rx link to parent of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # 8) remove a Tx link of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # Total number of actions = num_nodes * num_nodes + 1 + 1 + 1 + 4 * num_nodes * num_channel_offsets x slotframe_size
        # Total = 3 + num_nodes (num_nodes + 4 * num_channel_offsets x slotframe_size)
        n_actions = 3 + self.num_nodes * \
            (self.num_nodes + 4 * self.max_channel_offsets * self.max_slotframe_size)
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the current user requirements, routing paths, slotframe length, tsch schedules, RSSI and ETX network links.
        # 1) The user requirements is a vector of 1x3 Alpha, Beta, Gamma (ranges from 0 to 1)
        # 2) The routing path is a vector of the routes_matrix of shape num_nodes x num_nodes (1 represents a path between the two nodes)
        # 3) The slotframe length is a number (we can normalize it using the maximum length)
        # 4) The tsch schedules is a vector containing the schedules matrix for each node of size num_channel_offsets x slotframe_size
        # 5) The network RSSI links is a vector containing the current comm. link (size is num_nodes x num_nodes)
        # 6) The network ETX links is a vector containing the current link quality info (size is num_nodes x num_nodes)
        # Total number of observations = 3 + num_nodes x num_nodes + 1 + num_channel_offsets x slotframe_size x num_nodes + num_nodes x num_nodes + num_nodes x num_nodes
        # Total = 4 + num_nodes (num_nodes + num_channel_offsets x slotframe_size + num_nodes + num_nodes)
        # Total = 4 + num_nodes (3 * num_nodes + num_channel_offsets x slotframe_size)
        self.n_observations = 4 + \
            num_nodes * (3 * num_nodes + self.max_channel_offsets *
                         self.max_slotframe_size)
        self.observation_space = spaces.Box(low=0, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    def step(self, action):
        print("Performing action "+str(action))
        self.parser_action(action)
        observation = np.zeros(self.n_observations).astype(np.float32)
        reward = 1
        done = False
        info = {}
        return observation, reward, done, info

    def get_route_link(self, a):
        action = np.zeros(self.num_nodes*self.num_nodes)
        # set the corresponding action
        action[a] = 1
        # We now reshape the vector to a NxN matrix
        action_matrix = action.reshape(self.num_nodes, self.num_nodes)
        # We now get the indices
        scr, dst = np.where(action_matrix == 1.0)
        return scr[0], dst[0]

    def get_tsch_link(self, a, pos):
        # get the corresponding node ID
        pos = pos - self.num_nodes * self.max_channel_offsets * self.max_slotframe_size
        relative_pos = a - pos
        # print("relative_pos")
        # print(relative_pos)
        node_id = relative_pos // (self.max_channel_offsets *
                                   self.max_slotframe_size)
        # print("sensor node "+str(node_id))
        # get the corresponding ts and ch
        # get relative position to the current max ch and slot size
        relative_pos_tsch = relative_pos % (
            self.max_channel_offsets * self.max_slotframe_size)
        # print("relative_pos_tsch")
        # print(relative_pos_tsch)
        coordinates = np.zeros(self.max_channel_offsets *
                               self.max_slotframe_size)
        coordinates[relative_pos_tsch] = 1
        # We now reshape the vector to a NxN matrix
        coordinates_matrix = coordinates.reshape(
            self.max_channel_offsets, self.max_slotframe_size)
        # print("coordinates matrix")
        # print(coordinates_matrix)
        # We now get the indices
        ch, ts = np.where(coordinates_matrix == 1.0)
        # print("ts: "+str(ts)+" ch: "+str(ch))
        return node_id, ts[0], ch[0]

    def parser_action(self, a):
        pos = self.num_nodes * self.num_nodes - 1
        if a <= pos:
            scr, dst = self.get_route_link(a)
            print("adding link "+"("+str(scr)+","+str(dst)+")")
            return
        pos += 1
        if a <= pos:
            print("slotframe size one")
            return
        pos += 1
        if a <= pos:
            print("slotframe size two")
            return
        pos += 1
        if a <= pos:
            print("slotframe size three")
            return
        pos += self.num_nodes * self.max_channel_offsets * self.max_slotframe_size
        if a <= pos:
            node, ts, ch = self.get_tsch_link(a, pos)
            print("Adding a Rx link to node " + str(node) +
                  " at ts "+str(ts)+" ch "+str(ch))
            return
        pos += self.num_nodes * self.max_channel_offsets * self.max_slotframe_size
        if a <= pos:
            node, ts, ch = self.get_tsch_link(a, pos)
            print("Adding a Tx link to node " + str(node) +
                  " at ts "+str(ts)+" ch "+str(ch))
            return
        pos += self.num_nodes * self.max_channel_offsets * self.max_slotframe_size
        if a <= pos:
            node, ts, ch = self.get_tsch_link(a, pos)
            print("Removing a Rx link to node " + str(node) +
                  " at ts "+str(ts)+" ch "+str(ch))
            return
        node, ts, ch = self.get_tsch_link(a, pos)
        print("Removing a Tx link to node " + str(node) +
              " at ts "+str(ts)+" ch "+str(ch))
        return

    def dijkstra(self, G):
        # We want to compute the SP from all nodes to the controller
        path = {}
        for node in list(G.nodes):
            if node != 1 and node != 0:
                print("sp from node "+str(node))
                try:
                    node_path = nx.dijkstra_path(G, node, 1, weight='weight')
                    print("dijkstra path")
                    print(node_path)
                    path[node] = node_path
                    # TODO: find a way to avoid forcing the last addr of
                    # sensor nodes to 0.
                    self.routes.add_route(
                        str(node)+".0", "1.1", str(node_path[1])+".0")
                except nx.NetworkXNoPath:
                    print("path not found")
        self.routes.print_routes()
        print("total path")
        print(path)
        return path

    def mst(self, G):
        # We want to compute the MST of the current connected network
        # We call the edges "path"
        mst = nx.minimum_spanning_tree(
            G, algorithm="kruskal", weight="weight")
        return self.dijkstra(mst)

    def compute_algo(self, G, alg):
        # We first make sure the G is not empty
        if(nx.is_empty(G) == False):
            if(G.has_node(1)):  # Maybe use "1.0" instead
                print("graph has the controller")
                self.routes.clear_routes()
                match alg:
                    case "dijkstra":
                        print("running dijkstra")
                        path = self.dijkstra(G)
                    case "mst":
                        print("running MST")
                        path = self.mst(G)
        else:
            print("not able to compute routing, graph empty")
        return path

    def get_network_links(self):
        # Get last index of sensor
        N = get_last_index_wsn()+1
        # Neighbor matrix
        nbr_rssi_matrix = np.zeros(shape=(N, N))
        # We first loop through all sensor nodes
        nodes = Database.find(NODES_INFO, {})
        # nbr_etx_matrix = np.array([])
        for node in nodes:
            # Get last neighbors
            nbr = get_last_nbr(node["node_id"])
            if nbr is not None:
                for nbr_node in nbr:
                    source, _ = node["node_id"].split('.')
                    dst, _ = nbr_node["dst"].split('.')
                    nbr_rssi_matrix[int(source)][int(
                        dst)] = int(nbr_node["rssi"])
                    # nbr_etx_matrix[int(source)][int(
                    #     dst)] = int(nbr_node["etx"])
        matrix = nbr_rssi_matrix * -1
        G = nx.from_numpy_matrix(matrix, create_using=nx.DiGraph)
        G.remove_nodes_from(list(nx.isolates(G)))
        return G

    def build_routes_matrix(self, path):
        # Get last index of sensor
        N = get_last_index_wsn()+1
        routes_matrix = np.zeros(shape=(N, N))
        for u, p in path.items():
            if(len(p) >= 2):
                routes_matrix[p[0]][p[1]] = 1
        print("routing matrix")
        print(routes_matrix)
        # Save in DB
        current_time = datetime.now().timestamp() * 1000.0
        data = {
            "timestamp": current_time,
            "routes": routes_matrix.flatten().tolist()
        }
        Database.insert(ROUTING_PATHS, data)
        return routes_matrix

    def reset(self):
        """
        Important: the observation must be a numpy array
        :return: (np.array)
        """
        # The reset sets the routing and scheduling of the network
        # We support to initial states: shortest path and MST
        protocol = ["dijkstra", "mst"]
        # We get the network link, use to calculate the routing
        G = self.get_network_links()
        print("Current G")
        print(G.edges)
        print(G.nodes)
        protocol = random.choice(protocol)
        # Run the chosen algorithm with the current links
        path = self.compute_algo(G, protocol)
        # We now build and save the routing matrix
        self.build_routes_matrix(path)

        observation = np.zeros(self.n_observations).astype(np.float32)
        return observation  # reward, done, info can't be included

    def render(self, mode='human'):
        print("rendering")

    def close(self):
        pass
