""" This is the implementation of the Software-Defined Wireless Sensor Network
environment """
from controller.serial.serial_packet_dissector import *
from controller.routing.routes import Routes
from controller.centralised_scheduler.schedule import *
import random
# from scipy import rand
import networkx as nx
import gym
from gym import spaces
import numpy as np


class sdwsnEnv(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, num_nodes, max_channel_offsets, max_slotframe_size,
                 nc_job_queue, input_queue):
        super(sdwsnEnv, self).__init__()
        self.nc_job_queue = nc_job_queue
        self.input_queue = input_queue
        self.num_nodes = num_nodes
        self.max_channel_offsets = max_channel_offsets
        self.max_slotframe_size = max_slotframe_size
        # Keep track of the running routes
        self.routes = Routes()
        # Keep track of schedules
        self.schedule = Schedule(
            self.max_slotframe_size, max_channel_offsets)
        # We define the number of actions
        # 1) change parent node of a specific node (size: 1 * num_nodes * num_nodes)
        # 2) Increase slotframe size
        # 3) Decrease slotframe size
        # -- 4) change timeoffset of a specific node (size: 1 * num_nodes)
        # -- 5) change channeloffset of a specific node (size: 1 * num_nodes)
        # 4) add a new RX link of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size )
        # 5) add a new Tx link to parent of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # 6) remove a Rx link to parent of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # 7) remove a Tx link of a specific node (size: 1 * num_nodes * num_channel_offsets x slotframe_size)
        # Total number of actions = num_nodes * num_nodes + 1 + 1 + 4 * num_nodes * num_channel_offsets x slotframe_size
        # Total = 2 + num_nodes (num_nodes + 4 * num_channel_offsets x slotframe_size)
        # n_actions = 2 + self.num_nodes * \
        #     (self.num_nodes + 4 * self.max_channel_offsets * self.max_slotframe_size)
        n_actions = 2  # increase and decrease slotframe size
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the user requirements, energy, delay and pdr.
        self.n_observations = 3 + 1 + (num_nodes-1) * \
            max_channel_offsets * max_slotframe_size
        self.observation_space = spaces.Box(low=0, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    def step(self, action):
        # Get the current slotframe size
        sf_len, _ = self.get_slotframe_len()
        print("Performing action "+str(action))
        if action == 0:
            print("increasing slotframe size")
            sf_len += 1
        if action == 1:
            sf_len -= 1
            print("decreasing slotframe size")
        schedules_json = self.schedule.schedule_toJSON(sf_len)
        # Check if the current schedule job fits in the packet size 127 B
        while len(schedules_json['cells']) > 12:
            print("fragmentation is required for TSCH schedule job")
            extra_cells = schedules_json['cells'][12:]
            del schedules_json['cells'][12:]
            new_job = json.dumps(schedules_json, indent=4, sort_keys=True)
            self.nc_job_queue.put(new_job)
            del schedules_json['cells']
            schedules_json['cells'] = extra_cells
            schedules_json["sf_len"] = 0
        schedules_json = json.dumps(schedules_json, indent=4, sort_keys=True)
        # We now save the slotframe size in the SLOTFRAME_LEN collection
        self.save_slotframe_len(sf_len)
        self.nc_job_queue.put(schedules_json)
        # We now wait for the job to complete
        self.input_queue.get()
        print("process reward")
        # We get the observations now
        observation = self.get_observations()
        print(f"{len(observation)} observations received.")
        # self.parser_action(action)
        # We now process the reward
        user_req = self.get_last_user_requirements()
        power = self.get_network_power_consumption()
        delay = self.get_network_delay()
        pdr = self.get_network_pdr()
        reward = -1*(user_req[0]*power+user_req[1]*delay-user_req[2]*pdr)
        print(f'Reward {reward}')
        done = False
        info = {}
        return observation, reward, done, info

    """ Functions to process the observations """

    def get_observations(self):
        # 1) Get the current user requirements
        # 2) Get the overall energy
        # 3) Get the overall delay
        # 4) Get the overall pdr
        print("processing observations")
        # We start by getting the current user requirements
        user_req = self.get_last_user_requirements()
        array_user_req = np.array(user_req)
        # We now get the averaged network power consumption:
        # from the start of the deployment until just before selecting
        # the next action
        # power = self.get_network_power_consumption()
        # print("avg. power consumption")
        # print(power)
        # We now get the averaged network delay
        # delay = self.get_network_delay()
        # print("avg. delay")
        # print(delay)
        # We now get the averaged pdr since the last network reconfiguration
        # pdr = self.get_network_pdr()
        # print("avg. pdr")
        # print(pdr)
        # We now get the slotframe len
        _, sf_len = self.get_slotframe_len()
        array_sf_len = np.array(sf_len)
        # We now get the TSCH link schedules
        tsch_link_schedules = self.get_tsch_link_schedules()
        # We now concatenate all observations
        array_tsch_link_schedules = np.array(tsch_link_schedules)
        array_tsch_link_schedules = np.concatenate(
            array_tsch_link_schedules, axis=0)
        # Append all data together
        result = np.append(array_user_req, array_tsch_link_schedules)
        result = np.append(result, array_sf_len)

        return result

    def get_last_user_requirements(self):
        db = Database.find_one(USER_REQUIREMENTS, {})
        if db is None:
            return None
        # get last req in DB
        db = Database.find(USER_REQUIREMENTS, {}).sort("_id", -1).limit(1)
        for doc in db:
            return doc["requirements"]

    def get_start_time(self):
        # We get the last network configuration time from
        # the time stamp in the user requirements db
        db = Database.find_one(USER_REQUIREMENTS, {})
        if db is None:
            return None
        # get last req in DB
        db = Database.find(USER_REQUIREMENTS, {}).sort("_id", -1).limit(1)
        for doc in db:
            return doc["timestamp"]

    def get_last_n_power_consumption_samples(self, node, timestamp, energy_samples):
        query = {
            "$and": [
                {"node_id": node},
                {"energy": {"$exists": True}}
            ]
        }
        db = Database.find_one(NODES_INFO, query)
        if db is None:
            return None
        # Get last n samples after the timestamp
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$energy"},
            {"$match": {
                "energy.timestamp": {
                    "$gt": timestamp
                }
            }
            },
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$energy.timestamp',
                 'ewma_energy': '$energy.ewma_energy',
                 'ewma_energy_normalized': '$energy.ewma_energy_normalized'
             }
             }
        ]
        db = Database.aggregate(NODES_INFO, pipeline)
        for doc in db:
            energy_samples.append(doc["ewma_energy_normalized"])

    def get_network_power_consumption(self):
        # Get the time when the last network configuration was deployed
        timestamp = self.get_start_time()
        # Variable to keep track of the number of energy consumption samples
        energy_samples = []
        overall_energy = 0
        # We first loop through all sensor nodes
        nodes = Database.find(NODES_INFO, {})
        for node in nodes:
            # Get all samples from the start of the network configuration
            self.get_last_n_power_consumption_samples(
                node["node_id"], timestamp, energy_samples)
        print("energy samples")
        print(energy_samples)
        overall_energy = sum(energy_samples)/len(energy_samples)
        print("avg network power consumption for this cycle")
        print(overall_energy)
        return overall_energy

    def get_last_n_delay_samples(self, node, timestamp, delay_samples):
        query = {
            "$and": [
                {"node_id": node},
                {"delay": {"$exists": True}}
            ]
        }
        db = Database.find_one(NODES_INFO, query)
        if db is None:
            return None
        # Get last n samples after the timestamp
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$delay"},
            {"$match": {
                "delay.timestamp": {
                    "$gt": timestamp
                }
            }
            },
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$energy.timestamp',
                 'sampled_delay': '$delay.sampled_delay',
                 'ewma_delay': '$delay.ewma_delay',
                 'ewma_delay_normalized': '$delay.ewma_delay_normalized'
             }
             }
        ]
        db = Database.aggregate(NODES_INFO, pipeline)
        for doc in db:
            delay_samples.append(doc["ewma_delay_normalized"])

    def get_network_delay(self):
        # Get the time when the last network configuration was deployed
        timestamp = self.get_start_time()
        # Variable to keep track of the number of delay samples
        delay_samples = []
        overall_delay = 0
        # We first loop through all sensor nodes
        nodes = Database.find(NODES_INFO, {})
        for node in nodes:
            # Get all samples from the start of the network configuration
            self.get_last_n_delay_samples(
                node["node_id"], timestamp, delay_samples)
        print("delay samples")
        print(delay_samples)
        overall_delay = sum(delay_samples)/len(delay_samples)
        print("avg network delay for this cycle")
        print(overall_delay)
        return overall_delay

    def get_previous_pdr_seq_rcv(self, node, timestamp):
        query = {
            "$and": [
                {"node_id": node},
                {"pdr": {"$exists": True}}
            ]
        }
        db = Database.find_one(NODES_INFO, query)
        if db is None:
            return None
        # Get last heard sequence after the timestamp
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$pdr"},
            {"$match": {
                "pdr.timestamp": {
                    "$lt": timestamp
                }
            }
            },
            {"$sort": {"pdr.timestamp": -1}},
            {"$limit": 1},
            {'$project':
             {
                 "_id": 1,
                 'seq': '$pdr.seq'
             }
             }
        ]
        db = Database.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc["seq"]

    def get_last_n_pdr_samples(self, node, timestamp, pdr_samples):
        query = {
            "$and": [
                {"node_id": node},
                {"pdr": {"$exists": True}}
            ]
        }
        db = Database.find_one(NODES_INFO, query)
        if db is None:
            pdr_samples.append(0)
            return None
        # Let's get the previous data packet sequence
        last_seq = self.get_previous_pdr_seq_rcv(node, timestamp)
        if last_seq is None:
            last_seq = 0
        print("last sequence")
        print(last_seq)
        # Get last n samples after the timestamp
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$pdr"},
            {"$match": {
                "pdr.timestamp": {
                    "$gt": timestamp
                }
            }
            },
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$pdr.timestamp',
                 'seq': '$pdr.seq'
             }
             }
        ]
        db = Database.aggregate(NODES_INFO, pipeline)
        # Variable to keep track of the number rcv packets
        num_rcv = 0
        # Last received sequence
        last_seq_rcv = 0
        for doc in db:
            num_rcv += 1
            print("doc")
            print(doc)
            if (doc['seq'] > last_seq_rcv):
                last_seq_rcv = doc['seq']
        print("last seq recv")
        print(last_seq_rcv)
        print("num rcv")
        print(num_rcv)
        # Get the averaged pdr for this period
        if last_seq_rcv != 0:
            avg_pdr = num_rcv/(last_seq_rcv-last_seq)
        else:
            avg_pdr = 0
        print("avg pdr")
        print(avg_pdr)
        pdr_samples.append(avg_pdr)

    def get_network_pdr(self):
        # Get the time when the last network configuration was deployed
        timestamp = self.get_start_time()
        # Variable to keep track of the number of pdr samples
        pdr_samples = []
        overall_pdr = 0
        # We first loop through all sensor nodes
        nodes = Database.find(NODES_INFO, {})
        for node in nodes:
            print("calculating pdr for node " +
                  str(node["node_id"])+" timestamp "+str(timestamp))
            # Get all samples from the start of the network configuration
            self.get_last_n_pdr_samples(
                node["node_id"], timestamp, pdr_samples)
        print("pdr samples")
        print(pdr_samples)
        # Calculate the overall network pdr
        overall_pdr = sum(pdr_samples)/len(pdr_samples)
        print("avg network PDR for this cycle")
        print(overall_pdr)
        return overall_pdr

    def get_slotframe_len(self):
        db = Database.find_one(SLOTFRAME_LEN, {})
        if db is None:
            return None
        # get last req in DB
        db = Database.find(SLOTFRAME_LEN, {}).sort("_id", -1).limit(1)
        for doc in db:
            return (doc["len"], doc['normalized_len'])

    def get_tsch_link_schedules(self):
        db = Database.find_one(SCHEDULES, {})
        if db is None:
            return None
        # get last req in DB
        db = Database.find(SCHEDULES, {}).sort("_id", -1).limit(1)
        for doc in db:
            return doc["schedules"]

    """ Functions related to the step() function """

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

    """ The below functions are used by the env.reset() to establish the initial states """

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
            G.to_undirected(), algorithm="kruskal", weight="weight")
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
        N = self.num_nodes
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
        N = self.num_nodes
        routes_matrix = np.zeros(shape=(N, N))
        for _, p in path.items():
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

    def build_link_schedules_matrix(self):
        print("building link schedules matrix")
        # Get last index of sensor
        N = self.num_nodes
        # This is an array of schedule matrices
        link_schedules_matrix = [None] * N
        # We now loop through the entire array and fill it with the schedule information
        for node in self.schedule.list_nodes:
            # Construct the schedule matrix
            schedule = np.zeros(
                shape=(self.schedule.num_channel_offsets, self.schedule.slotframe_size))
            for rx_cell in node.rx:
                # print("node is listening in ts " +
                #       str(rx_cell.timeoffset)+" ch "+str(rx_cell.channeloffset))
                schedule[rx_cell.channeloffset][rx_cell.timeoffset] = 1
            for tx_cell in node.tx:
                # print("node is transmitting in ts " +
                #       str(tx_cell.timeoffset)+" ch "+str(tx_cell.channeloffset))
                schedule[tx_cell.channeloffset][tx_cell.timeoffset] = -1
            addr = node.node.split(".")
            link_schedules_matrix[int(
                addr[0])] = schedule.flatten().tolist()
        # print("link_schedules_matrix")
        # print(link_schedules_matrix)
        # using list comprehension
        # to remove None values in list
        res = [i for i in link_schedules_matrix if i]
        # Save in DB
        current_time = datetime.now().timestamp() * 1000.0
        data = {
            "timestamp": current_time,
            "schedules": res
        }
        Database.insert(SCHEDULES, data)
        return res

    def save_slotframe_len(self, slotframe_size):
        current_time = datetime.now().timestamp() * 1000.0
        normalized_sf_size = slotframe_size / self.schedule.slotframe_size
        data = {
            "timestamp": current_time,
            "len": slotframe_size,
            "normalized_len": normalized_sf_size,
        }
        Database.insert(SLOTFRAME_LEN, data)

    def compute_schedule_for_routing(self, path, slotframe_size):
        self.schedule.clear_schedule()
        for _, p in path.items():
            if(len(p) >= 2):
                # print("try to add uc for ", p)
                for i in range(len(p)-1):
                    # TODO: find a way to avoid forcing the last addr of
                    # sensor nodes to 0.
                    node = p[i+1]
                    node = str(node)+".0"
                    neighbor = p[i]
                    neighbor = str(neighbor)+".0"
                    # print("rx ", str(node), "tx: ", str(neighbor))
                    timeslot = random.randrange(0,
                                                slotframe_size-1)
                    channeloffset = random.randrange(0,
                                                     self.schedule.num_channel_offsets-1)
                    self.schedule.add_uc(
                        str(node), cell_type.UC_RX, channeloffset, timeslot)
                    self.schedule.add_uc(
                        str(neighbor), cell_type.UC_TX, destination=node)

            else:
                # print("add an uc rx for node ", p[0])
                timeslot = random.randrange(0, slotframe_size-1)
                channeloffset = random.randrange(0,
                                                 self.schedule.num_channel_offsets-1)
                self.schedule.add_uc(
                    p[0], cell_type.UC_RX, channeloffset, timeslot)
        self.schedule.print_schedule()

    def user_requirements(self, req):
        user_req = np.array(req)
        current_time = datetime.now().timestamp() * 1000.0
        data = {
            "timestamp": current_time,
            "requirements": user_req.flatten().tolist()
        }
        Database.insert(USER_REQUIREMENTS, data)

    def reset(self):
        """
        Important: the observation must be a numpy array
        :return: (np.array)
        """
        # The reset sets the routing and scheduling
        # We support to initial states: shortest path and MST
        protocol = ["dijkstra", "mst"]
        # We get the network links, we use them to calculate the routing
        G = self.get_network_links()
        print("Current G")
        print(G.edges)
        print(G.nodes)
        # We randomly pick any of the two protocols
        protocol = random.choice(protocol)
        # Run the chosen algorithm with the current links
        path = self.compute_algo(G, protocol)
        # We now build and save the routing matrix
        self.build_routes_matrix(path)
        # We randomly pick a slotframe size between 10, 17 or 31
        slotframe_sizes = [17, 31]
        slotframe_size = random.choice(slotframe_sizes)
        # We now set the TSCH schedules for the current routing
        self.compute_schedule_for_routing(path, slotframe_size)
        # We now save the slotframe size in the SLOTFRAME_LEN collection
        self.save_slotframe_len(slotframe_size)
        # We now save the TSCH schedules
        self.build_link_schedules_matrix()
        # We now set and save the user requirements
        balanced = [0.35, 0.3, 0.3]
        energy = [0.5, 0.25, 0.25]
        delay = [0.25, 0.5, 0.25]
        reliability = [0.25, 0.25, 0.5]
        user_req = [balanced, energy, delay, reliability]
        select_user_req = random.choice(user_req)
        self.user_requirements(select_user_req)
        # Let's prepare the schedule information in the json format
        schedules_json = self.schedule.schedule_toJSON(slotframe_size)
        print("json")
        print(json.dumps(schedules_json, indent=4, sort_keys=True))
        # Check if the current schedule job fits in the packet size 127 B
        while len(schedules_json['cells']) > 12:
            print("fragmentation is required for TSCH schedule job")
            extra_cells = schedules_json['cells'][12:]
            del schedules_json['cells'][12:]
            new_job = json.dumps(schedules_json, indent=4, sort_keys=True)
            self.nc_job_queue.put(new_job)
            del schedules_json['cells']
            schedules_json['cells'] = extra_cells
            schedules_json["sf_len"] = 0
        schedules_json = json.dumps(schedules_json, indent=4, sort_keys=True)
        # Let's prepare the routing information in the json format
        routes_json = self.routes.routes_toJSON()
        # We send the jobs but we don't need the whole cycle to complete
        # as we are not returning the reward.
        self.nc_job_queue.put(schedules_json)
        self.nc_job_queue.put(routes_json)
        # We get the observations now
        observation = self.get_observations()
        print(f"{len(observation)} observations received.")
        # observation = np.zeros(self.n_observations).astype(np.float32)
        return observation  # reward, done, info can't be included

    def render(self, mode='human'):
        print("rendering")

    def close(self):
        pass
