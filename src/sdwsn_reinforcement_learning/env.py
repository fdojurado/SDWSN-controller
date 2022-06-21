""" This is the implementation of the Software-Defined Wireless Sensor Network
environment """
import imp
import random
# from scipy import rand
from random import randrange
import networkx as nx
import gym
from gym import spaces
import numpy as np
import json
from time import sleep
from datetime import datetime
from pymongo.collation import Collation
import threading

from sdwsn_common import common
from sdwsn_packet import packet_dissector
from sdwsn_tsch.schedule import Schedule
from sdwsn_routes.routes import Routes
from sdwsn_database.database import NODES_INFO
from sdwsn_tsch.contention_free_scheduler import contention_free_schedule
from sdwsn_database.database import OBSERVATIONS
from sdwsn_packet.packet_dissector import SLOT_DURATION

# These are the size of other schedules in orchestra
eb_size = 397
common_size = 31
control_plane_size = 27


class Env(gym.Env):
    """Custom SDWSN Environment that follows gym interface"""
    metadata = {'render.modes': ['human']}

    def __init__(self, packet_dissector, network_reconfiguration, container, ser, max_channel_offsets=3,
                 max_slotframe_size=100, processing_window=200):
        super(Env, self).__init__()
        self.packet_dissector = packet_dissector
        self.nc = network_reconfiguration
        self.max_channel_offsets = max_channel_offsets
        self.max_slotframe_size = max_slotframe_size
        self.processing_window = processing_window
        self.container = container
        self.ser = ser
        self._read_ser_thread = threading.Thread(target=self._read_ser)
        # Keep track of the running routes
        self.routes = Routes()
        # Keep track of schedules
        self.schedule = Schedule(
            self.max_slotframe_size, max_channel_offsets)
        # We define the number of actions
        n_actions = 2  # increase and decrease slotframe size
        self.action_space = spaces.Discrete(n_actions)
        # We define the observation space
        # They will be the user requirements, last ts, SF size and normalized ts in schedule
        self.n_observations = 6
        self.observation_space = spaces.Box(low=0, high=1,
                                            shape=(self.n_observations, ), dtype=np.float32)

    """ Step action """

    def step(self, action):
        # We now get the last observations
        alpha, beta, delta, last_ts_in_schedule, current_sf_len, normalized_ts_in_schedule, _ = self.get_last_observations()
        # Get the current slotframe size
        sf_len = current_sf_len
        print("Performing action "+str(action))
        if action == 0:
            print("increasing slotframe size")
            sf_len = common.next_coprime(sf_len)
        if action == 1:
            sf_len = common.previous_coprime(sf_len)
            print("decreasing slotframe size")
            # Lets verify that the SF size is greater than
        # the last slot in the current schedule
        if (sf_len > last_ts_in_schedule):
            schedules_json = self.schedule.schedule_toJSON(sf_len)
            # Save the time of performing the action
            sample_time = datetime.now().timestamp() * 1000.0
            # Check if the current schedule job fits in the packet size 127 B
            while len(schedules_json['cells']) > 12:
                print("fragmentation is required for TSCH schedule job")
                extra_cells = schedules_json['cells'][12:]
                del schedules_json['cells'][12:]
                new_job = json.dumps(schedules_json, indent=4, sort_keys=True)
                # set job id
                self.packet_dissector.cycle_sequence += 1
                # Send job with id and wait for reply
                self.send_job(new_job, self.packet_dissector.cycle_sequence)
                self.packet_dissector.sequence = 0
                del schedules_json['cells']
                schedules_json['cells'] = extra_cells
                schedules_json["sf_len"] = 0

            schedules_json = json.dumps(
                schedules_json, indent=4, sort_keys=True)
            # We now save the slotframe size in the SLOTFRAME_LEN collection
            # self.save_slotframe_len(sf_len)
            # set job id
            self.packet_dissector.cycle_sequence += 1
            # Send job with id and wait for reply
            self.send_job(schedules_json, self.packet_dissector.cycle_sequence)
            self.packet_dissector.sequence = 0
            # We now wait for the cycle to complete
            while(1):
                if self.packet_dissector.sequence > self.processing_window:
                    break
                sleep(0.1)
            print("process reward")
            sleep(1)
            # Build observations
            user_requirements = np.array([alpha, beta, delta])
            observation = np.append(user_requirements, last_ts_in_schedule)
            observation = np.append(observation, sf_len)
            observation = np.append(observation, normalized_ts_in_schedule)
            # Calculate the reward
            reward, power, delay, pdr = self.calculate_reward(
                sample_time, alpha, beta, delta)
            print(f'Reward {reward}')
            self.save_observations(
                sample_time, alpha, beta, delta, power[0], power[1], power[2],
                delay[0], delay[1], delay[2],
                pdr[0], pdr[1],
                last_ts_in_schedule, sf_len, normalized_ts_in_schedule,
                reward)
            # self.parser_action(action)
            done = False
            info = {}
            return observation, reward, done, info
        else:
            # Penalty for going below the last ts in the schedule
            # Build observations
            user_requirements = np.array([alpha, beta, delta])
            observation = np.append(user_requirements, last_ts_in_schedule)
            observation = np.append(observation, sf_len)
            observation = np.append(observation, normalized_ts_in_schedule)
            done = False
            info = {}
            return observation, -3, done, info

    """ Get observations """

    def get_last_observations(self):
        db = self.packet_dissector.db.find_one(OBSERVATIONS, {})
        if db is None:
            return None
        # get last req in DB
        db = self.packet_dissector.db.find(
            OBSERVATIONS, {}).sort("_id", -1).limit(1)
        for doc in db:
            alpha = doc["alpha"]
            beta = doc["beta"]
            delta = doc["delta"]
            last_ts_in_schedule = doc['last_ts_in_schedule']
            current_sf_len = doc['current_sf_len']
            normalized_ts_in_schedule = doc['normalized_ts_in_schedule']
            reward = doc['reward']
            return alpha, beta, delta, last_ts_in_schedule, current_sf_len, normalized_ts_in_schedule, reward

    """ Reward calculation methods """

    def get_sensor_nodes_in_order(self):
        db = self.packet_dissector.db.find(NODES_INFO, {}).sort("node_id").collation(
            Collation(locale="en_US", numericOrdering=True))
        nodes = []
        if db is None:
            return None
        for node in db:
            nodes.append(node["node_id"])
        return nodes

    def calculate_reward(self, init_time, alpha, beta, delta):
        # Get the sensor nodes to loop in ascending order
        nodes = self.get_sensor_nodes_in_order()
        # Get the normalized average power consumption for this cycle
        power_wam, power_mean, power_normalized = self.get_network_power_consumption(
            init_time, nodes)
        power = [power_wam, power_mean, power_normalized]
        # Get the normalized average delay for this cycle
        delay_wam, delay_mean, delay_normalized = self.get_network_delay(
            init_time, nodes)
        delay = [delay_wam, delay_mean, delay_normalized]
        # Get the normalized average pdr for this cycle
        pdr_wam, pdf_mean = self.get_network_pdr(init_time, nodes)
        pdr = [pdr_wam, pdf_mean]
        # Calculate the reward
        reward = -1*(alpha*power_normalized+beta *
                     delay_normalized-delta*pdr_wam)
        return reward, power, delay, pdr

    """ Power consumption processing methods """

    def power_compute_wam_weight(self, node):
        # Let's first get the rank of the sensor node
        node_rank = self.packet_dissector.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.packet_dissector.db.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Let's get the number of neighbors
        num_nbr = 0
        for _ in self.packet_dissector.get_last_nbr(node):
            num_nbr += 1
        # Get the total number of sensor nodes
        N = self.packet_dissector.get_number_of_sensors()
        # Calculate the weight
        weight = 0.9 * (node_rank/last_rank) + 0.1 * (num_nbr/N)
        # print(f'computing WAM of node {node} rank {node_rank} num nbr {num_nbr} N {N} weight {weight}')
        return weight

    def power_weighted_arithmetic_mean(self, power_samples):
        weights = []
        all_power_samples = []
        for elem in power_samples:
            node = elem[0]
            power = elem[1]
            all_power_samples.append(power)
            # print(f'Finding the WAM of {node} with power {power}')
            weight = self.power_compute_wam_weight(node)
            weights.append(weight)
        print(f'power all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_power = np.array(all_power_samples)
        all_power_transpose = np.transpose(all_power)
        # print(f'transpose all power {all_power_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_power_transpose)
        # Overall network mean
        normal_mean = all_power.sum()/len(all_power_samples)
        print(f'power network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def get_last_power_consumption(self, node, power_samples):
        query = {
            "$and": [
                {"node_id": node},
                {"energy": {"$exists": True}}
            ]
        }
        db = self.packet_dissector.db.find_one(NODES_INFO, query)
        if db is None:
            return None
        # Get last n samples after the timestamp
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$energy"},
            {"$match": {
                "energy.cycle_seq": {
                    "$eq": self.packet_dissector.cycle_sequence
                }
            }
            },
            {"$sort": {"energy.timestamp": -1}},
            {"$limit": 1},
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$energy.timestamp',
                 'ewma_energy': '$energy.ewma_energy',
                 #  'ewma_energy_normalized': '$energy.ewma_energy_normalized'
             }
             }
        ]
        db = self.packet_dissector.db.aggregate(NODES_INFO, pipeline)

        energy = 0
        for doc in db:
            energy = doc['ewma_energy']
            print("last energy sample")
            print(energy)
        # Calculate the avg delay
        if energy > 0:
            power_samples.append((node, energy))
        else:
            power_samples.append((node, 3000))
        return

    def get_network_power_consumption(self, init_time, nodes):
        # Min power
        p_min = 0
        # Max power
        p_max = 3000
        # Get the time when the last network configuration was deployed
        timestamp = init_time
        # Variable to keep track of the number of energy consumption samples
        power_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            print(f"printing power for node {node}")
            # Get all samples from the start of the network configuration
            self.get_last_power_consumption(
                node, power_samples)
        print(f"power samples for sequence {self.packet_dissector.cycle_sequence}")
        print(power_samples)
        # We now need to compute the weighted arithmetic mean
        power_wam, power_mean = self.power_weighted_arithmetic_mean(
            power_samples)
        # We now need to normalize the power WAM
        normalized_power = (power_wam - p_min)/(p_max-p_min)
        print(f'normalized power {normalized_power}')
        return power_wam, power_mean, normalized_power

    """ Delay processing methods """

    def delay_compute_wam_weight(self, node):
        # print(f'computing delay WAM of node {node}')
        # We assume that the wight depends on the rank
        # Let's get the rank of the sensor node
        node_rank = self.packet_dissector.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.packet_dissector.db.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Calculate the weight
        weight = 1 - node_rank/(last_rank+1)
        # print(f'computing WAM of node {node} rank {node_rank} weight {weight}')
        return weight

    def delay_weighted_arithmetic_mean(self, delay_samples):
        weights = []
        all_delay_samples = []
        for elem in delay_samples:
            node = elem[0]
            delay = elem[1]
            all_delay_samples.append(delay)
            # print(f'Finding the WAM of {node} with delay {delay}')
            weight = self.delay_compute_wam_weight(node)
            weights.append(weight)
        print(f'delay all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_delay = np.array(all_delay_samples)
        all_delay_transpose = np.transpose(all_delay)
        # print(f'transpose all delay {all_delay_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_delay_transpose)
        # Overall network mean
        normal_mean = all_delay.sum()/len(all_delay_samples)
        print(f'delay network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def get_avg_delay(self, node, delay_samples):
        query = {
            "$and": [
                {"node_id": node},
                {"delay": {"$exists": True}}
            ]
        }
        db = self.packet_dissector.db.find_one(NODES_INFO, query)
        if db is None:
            return None
        # Get last n samples after the timestamp
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$delay"},
            {"$match": {
                "delay.cycle_seq": {
                    "$gte": self.packet_dissector.cycle_sequence
                }
            }
            },
            {'$project':
             {
                 "_id": 1,
                 "cycle_seq": '$delay.cycle_seq',
                 "seq": '$delay.seq',
                 'sampled_delay': '$delay.sampled_delay',
             }
             }
        ]
        # Variable to keep track of the number samples
        num_rcv = 0
        # Sum of delays
        sum_delay = 0

        db = self.packet_dissector.db.aggregate(NODES_INFO, pipeline)

        for doc in db:
            delay = doc["sampled_delay"]
            # print("sample delay")
            # print(delay)
            num_rcv += 1
            sum_delay += delay

        # Calculate the avg delay
        if num_rcv > 0:
            avg_delay = sum_delay/num_rcv
        else:
            avg_delay = 2500
        delay_samples.append((node, avg_delay))
        return

    def get_network_delay(self, init_time, nodes):
        # Min power
        delay_min = SLOT_DURATION
        # Max power
        delay_max = 2500
        # Get the time when the last network configuration was deployed
        timestamp = init_time
        # Variable to keep track of the number of delay samples
        delay_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            # print(f"printing delay for node {node}")
            # Get all samples from the start of the network configuration
            self.get_avg_delay(
                node, delay_samples)
        print(f"delay samples for sequence {self.packet_dissector.cycle_sequence}")
        print(delay_samples)
        # We now need to compute the weighted arithmetic mean
        delay_wam, delay_mean = self.delay_weighted_arithmetic_mean(
            delay_samples)
        # We now need to normalize the power WAM
        normalized_delay = (delay_wam - delay_min)/(delay_max-delay_min)
        print(f'normalized delay {normalized_delay}')
        return delay_wam, delay_mean, normalized_delay

    """ PDR processing methods """

    def pdr_compute_wam_weight(self, node):
        # print(f'computing WAM of node {node}')
        # We assume that the wight depends on the rank of
        # the node and the number of NBRs
        # Let's first get the rank of the sensor node
        node_rank = self.packet_dissector.get_rank(node)
        # Get the value of the greatest rank of the network
        db = self.packet_dissector.db.find_one(
            NODES_INFO, {}, sort=[("rank", -1)])
        last_rank = db['rank']
        # Let's get the number of neighbors
        num_nbr = 0
        for _ in self.packet_dissector.get_last_nbr(node):
            num_nbr += 1
        # Get the total number of sensor nodes
        N = self.packet_dissector.get_number_of_sensors()
        # Calculate the weight
        weight = 0.9 * (node_rank/last_rank) + 0.1 * (num_nbr/N)
        # print(f'computing pdr WAM of node {node} rank {node_rank} num nbr {num_nbr} N {N} weight {weight}')
        return weight

    def pdr_weighted_arithmetic_mean(self, pdr_samples):
        weights = []
        all_pdr_samples = []
        for elem in pdr_samples:
            node = elem[0]
            pdr = elem[1]
            all_pdr_samples.append(pdr)
            # print(f'Finding the WAM of {node} with pdr {pdr}')
            weight = self.pdr_compute_wam_weight(node)
            weights.append(weight)
        print(f'pdr all weights {weights}')
        weights_np = np.array(weights)
        sum_weights = weights_np.sum()
        # print(f'sum of weights {sum_weights}')
        normalized_weights = weights_np/sum_weights
        print(f'normalized weights {normalized_weights}')
        all_pdr = np.array(all_pdr_samples)
        all_pdr_transpose = np.transpose(all_pdr)
        # print(f'transpose all pdr {all_pdr_transpose}')
        # WAM
        wam = np.dot(normalized_weights, all_pdr_transpose)
        # Overall network mean
        normal_mean = all_pdr.sum()/len(all_pdr_samples)
        print(f'pdr network WAM {wam} normal mean {normal_mean}')
        return wam, normal_mean

    def get_avg_pdr(self, node, pdr_samples):
        query = {
            "$and": [
                {"node_id": node},
                {"pdr": {"$exists": True}}
            ]
        }
        db = self.packet_dissector.db.find_one(NODES_INFO, query)
        if db is None:
            pdr_samples.append(0)
            return None
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$pdr"},
            {"$match": {
                "pdr.cycle_seq": {
                    "$gte": self.packet_dissector.cycle_sequence
                }
            }
            },
            {'$project':
             {
                 "_id": 1,
                 "cycle_seq": '$pdr.cycle_seq',
                 "seq": '$pdr.seq'
             }
             }
        ]
        db = self.packet_dissector.db.aggregate(NODES_INFO, pipeline)
        # Variable to keep track of the number rcv packets
        num_rcv = 0
        # Last received sequence
        seq = 0
        for doc in db:
            seq = doc['seq']
            num_rcv += 1
        # print(f"last sequence received {last_seq_rcv}")
        # Get the averaged pdr for this period
        if seq > 0:
            avg_pdr = num_rcv/seq
        else:
            avg_pdr = 0
        if avg_pdr > 1.0:
            avg_pdr = 1.0
        pdr_samples.append((node, avg_pdr))
        return

    def get_network_pdr(self, init_time, nodes):
        # Variable to keep track of the number of pdr samples
        pdr_samples = []
        # We first loop through all sensor nodes
        for node in nodes:
            # print(f"printing pdr for node {node}")
            # Get all samples from the start of the network configuration
            self.get_avg_pdr(
                node, pdr_samples)
        print(f"pdr samples for sequence {self.packet_dissector.cycle_sequence}")
        print(pdr_samples)
        # We now need to compute the weighted arithmetic mean
        pdr_wam, pdr_mean = self.pdr_weighted_arithmetic_mean(
            pdr_samples)
        print(f'normalized pdr {pdr_wam}')
        return pdr_wam, pdr_mean

    """ Reset the environment, reset the routing and the TSCH schedules """

    def _read_ser(self):
        while(1):
            try:
                msg = self.ser.recv(0.1)
                if(len(msg) > 0):
                    self.packet_dissector.handle_serial_packet(msg)
            except TypeError:
                pass

    def stop_serial(self):
        self._read_ser_thread.stop()

    def _serial_start(self):
        # Connect serial
        if self.ser.connect() != 0:
            print('unsuccessful serial connection')
            return 0
        # Read serial
        if not self._read_ser_thread.is_alive():
            self._read_ser_thread.start()
        return 1

    def reset(self):
        # Reset the database
        self.packet_dissector.db.initialise()
        self.packet_dissector.cycle_sequence = 0
        self.packet_dissector.sequence = 0
        # We start and run the container application first
        self.container.start_container()
        print(f'status: {self.container.status()}')
        # We now wait until the socket is active in Cooja
        self.container.wait_socket_running()
        # Start the serial interface
        if not self._serial_start():
            print('unable to start serial interface')
        print("serial interface up and running")
        # We now wait until we reach the processing_window
        while(1):
            if self.packet_dissector.sequence > self.processing_window:
                break
            sleep(0.1)
        # We get the network links, useful when calculating the routing
        G = common.get_network_links(self.packet_dissector)
        # Run the chosen algorithm with the current links
        path = common.compute_algo(G, "dijkstra", self.routes)
        # Set the slotframe size
        slotframe_size = 23
        # We now set the TSCH schedules for the current routing
        contention_free_schedule(self.schedule, path, slotframe_size)
        # We now set and save the user requirements
        select_user_req = [0.8, 0.1, 0.1]
        # Let's prepare the schedule information in the json format
        schedules_json = self.schedule.schedule_toJSON(slotframe_size)
        print("json")
        print(json.dumps(schedules_json, indent=4, sort_keys=True))
        while len(schedules_json['cells']) > 12:
            print("fragmentation is required for TSCH schedule job")
            extra_cells = schedules_json['cells'][12:]
            del schedules_json['cells'][12:]
            new_job = json.dumps(schedules_json, indent=4, sort_keys=True)
            # set job id
            self.packet_dissector.cycle_sequence += 1
            # Send job with id and wait for reply
            self.send_job(new_job, self.packet_dissector.cycle_sequence)
            self.packet_dissector.sequence = 0
            del schedules_json['cells']
            schedules_json['cells'] = extra_cells
            schedules_json["sf_len"] = 0

        schedules_json = json.dumps(schedules_json, indent=4, sort_keys=True)
        # Let's prepare the routing information in the json format
        routes_json = self.routes.routes_toJSON()
        # set job id
        self.packet_dissector.cycle_sequence += 1
        # Send job with id and wait for reply
        self.send_job(schedules_json, self.packet_dissector.cycle_sequence)
        self.packet_dissector.sequence = 0
        # set job id
        self.packet_dissector.cycle_sequence += 1
        # Send job with id and wait for reply
        self.send_job(routes_json, self.packet_dissector.cycle_sequence)
        self.packet_dissector.sequence = 0
        # Wait for the network to settle
        sleep(0.5)
        # We now save all the observations
        # They are of the form "time, user requirements, routing matrix, schedules matrix, sf len"
        sample_time = datetime.now().timestamp() * 1000.0
        # We now save the user requirements
        user_requirements = np.array(select_user_req)
        # We now build the TSCH schedule matrix
        _, last_ts = common.build_link_schedules_matrix_obs(
            self.packet_dissector, self.schedule)
        ts_in_schedule = self.schedule.get_list_ts_in_use()
        sum = 0
        for ts in ts_in_schedule:
            sum += 2**ts
        normalized_ts_in_schedule = sum/(2**slotframe_size)
        # We now save the observations with reward None
        # observation = np.zeros(self.n_observations).astype(np.float32)
        # slotframe_size = slotframe_size + 15
        observation = np.append(user_requirements, last_ts)
        observation = np.append(observation, slotframe_size)
        observation = np.append(observation, normalized_ts_in_schedule)
        self.save_observations(
            sample_time, select_user_req[0], select_user_req[1], select_user_req[2],
            None, None, None,
            None, None, None,
            None, None,
            last_ts, slotframe_size, normalized_ts_in_schedule,
            None)
        return observation  # reward, done, info can't be included

    # Send to the SDWSN
    def send_job(self, data, job_id):
        # Send the job to the NC process
        result = self.nc.send_nc(data, job_id)
        if result == 0:
            print("job did not completed")

    """ Save observations """

    def save_observations(self, timestamp, alpha, beta, delta,
                          power_wam, power_mean, power_normalized,
                          delay_wam, delay_mean, delay_normalized,
                          pdr_wam, pdr_mean,
                          last_ts_in_schedule, current_sf_len, normalized_ts_in_schedule,
                          reward):
        data = {
            "timestamp": timestamp,
            "alpha": alpha,
            "beta": beta,
            "delta": delta,
            "power_wam": power_wam,
            "power_avg": power_mean,
            "power_normalized": power_normalized,
            "delay_wam": delay_wam,
            "delay_avg": delay_mean,
            "delay_normalized": delay_normalized,
            "pdr_wam": pdr_wam,
            "pdr_mean": pdr_mean,
            "last_ts_in_schedule": last_ts_in_schedule,
            "current_sf_len": current_sf_len,
            "normalized_ts_in_schedule": normalized_ts_in_schedule,
            "reward": reward
        }
        self.packet_dissector.db.insert(OBSERVATIONS, data)
