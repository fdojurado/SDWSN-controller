#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from sdwsn_controller.database.database import Database, PACKETS, NODES_INFO, OBSERVATIONS, SLOTFRAME_LEN
from sdwsn_controller.packet.packet import SDN_NAPL_LEN, NA_Packet_Payload
import json
from datetime import datetime
import numpy as np
import pandas as pd
from pymongo.collation import Collation
import pymongo

# Network parameters
H_MAX = 10  # max number of hops
#  EWMA (exponential moving average) used to maintain statistics over time
EWMA_SCALE = 100
EWMA_ALPHA = 40
# Sensor nodes electrical parameters references
VOLTAGE = 3
I_LPM = 0.545  # mA
# I_TX = 17.4  # mA
I_RX = 20  # mA
# Constants for energy normalization
# ENERGY_SAMPLE_DURATION = 10  # seconds
PMIN = 0  # Value in micro
PMAX = VOLTAGE * I_RX * 1.2 * 1e3  # Value in micro
MIN_TX = PMAX/3  # Max energy for the last node in the network
# Constants for packet delay calculation
SLOT_DURATION = 10
NUM_SLOTS = 17
Q_MAX = 4  # Maximum size of the queue
R_MAX = 3   # Maximum number of retransmissions
SLOTFRAME_SIZE = NUM_SLOTS * SLOT_DURATION  # Size of the dataplane slotframe


class DatabaseManager(Database):
    def __init__(
        self,
        name: str = 'mySDN',
        host: str = '127.0.0.1',
        port: int = 27017
    ):
        assert isinstance(name, str)
        assert isinstance(host, str)
        assert isinstance(port, int)
        self.name = name
        self.host = host
        self.port = port
        self.URI = "mongodb://"+host+":"+str(port)
        self.DATABASE = None
        super().__init__()

    def initialize(self):
        self.client = pymongo.MongoClient(self.URI)
        self.client.drop_database(self.name)
        self.DATABASE = self.client[self.name]

    def DATABASE(self):
        return self.DATABASE

    def export_collection(self, collection, name, folder):
        db = self.find_one(collection, {})
        if db is None:
            return
        # Load collection
        data = self.find(collection, {})
        # Expand the cursor and construct the DataFrame
        df = pd.DataFrame(data)
        df.to_csv(folder+name+'.csv')

    def delete_info_collection(self):
        self.delete_collection(NODES_INFO)

    def get_observations(self):
        db = self.find_one(OBSERVATIONS, {})
        if db is None:
            print("Observation collection doesn't exist")
            return None
        return self.find(OBSERVATIONS, {})

    def save_serial_packet(self, pkt):
        # The incoming format should be JSON
        data = json.loads(pkt)
        data["timestamp"] = datetime.now().timestamp() * 1000.0
        self.insert_one(PACKETS, data)

    def save_energy(self, pkt, na_pkt):
        current_time = datetime.now().timestamp() * 1000.0
        data = {
            "timestamp": current_time,
            "cycle_seq": na_pkt.cycle_seq,
            "seq": na_pkt.seq,
            "ewma_energy": na_pkt.energy
        }
        update = {
            "$push": {
                "energy": data
            }
        }
        filter = {
            "node_id": pkt.scrStr
        }
        self.update_one(NODES_INFO, filter, update, True, None)
        # Database.update_one(NODES_INFO, filter, update, True, None)
        # Set the rank
        update = {
            "$set": {
                "rank": na_pkt.rank
            }
        }
        filter = {
            "node_id": pkt.scrStr
        }
        self.update_one(NODES_INFO, filter, update, True, None)

    def save_neighbors(self, pkt, na_pkt):
        # """ Let's process NA payload """
        current_time = datetime.now().timestamp() * 1000.0
        # Process neighbors
        blocks = len(na_pkt.payload) // SDN_NAPL_LEN
        idx_start = 0
        idx_end = 0
        for x in range(1, blocks+1):
            idx_end += SDN_NAPL_LEN
            payload = na_pkt.payload[idx_start:idx_end]
            idx_start = idx_end
            payload_unpacked = NA_Packet_Payload.unpack(payload)
            data = {
                'timestamp': current_time,
                'dst': payload_unpacked.addrStr,
                'rssi': payload_unpacked.rssi,
                'etx': payload_unpacked.etx,
            }
            update = {
                "$push": {
                    "neighbors": data
                }
            }
            filter = {
                "node_id": pkt.scrStr
            }
            self.update_one(NODES_INFO, filter, update, True, None)

    def save_pdr(self, pkt, data_pkt):
        current_time = datetime.now().timestamp() * 1000.0
        data = {
            "timestamp": current_time,
            "cycle_seq": data_pkt.cycle_seq,
            "seq": data_pkt.seq,
        }
        update = {
            "$push": {
                "pdr": data
            }
        }
        filter = {
            "node_id": pkt.scrStr
        }
        self.update_one(NODES_INFO, filter, update, True, None)

    def save_delay(self, pkt, data_pkt):
        current_time = datetime.now().timestamp() * 1000.0
        sampled_delay = data_pkt.asn * SLOT_DURATION
        data = {
            "timestamp": current_time,
            "cycle_seq": data_pkt.cycle_seq,
            "seq": data_pkt.seq,
            "sampled_delay": sampled_delay
        }
        update = {
            "$push": {
                "delay": data
            }
        }
        filter = {
            "node_id": pkt.scrStr
        }
        self.update_one(NODES_INFO, filter, update, True, None)

    def get_rank(self, addr):
        if (addr == "1.0"):
            return 0
        query = {
            "$and": [
                {"node_id": addr},
                {"rank": {"$exists": True}}
            ]
        }
        db = self.find_one(NODES_INFO, query)
        if db is None:
            return
        else:
            return db["rank"]

    def greatest_rank(self):
        return self.find_one(NODES_INFO, {}, sort=[("rank", -1)])

    def get_last_slotframe_len(self):
        db = self.find_one(SLOTFRAME_LEN, {})
        if db is None:
            return None
        # get last seq in DB
        db = self.find(SLOTFRAME_LEN, {}).sort("_id", -1).limit(1)
        for doc in db:
            return doc["slotframe_len"]

    # def get_last_power_consumption(self, node):
    #     query = {
    #         "$and": [
    #             {"node_id": node},
    #             {"energy": {"$exists": True}}
    #         ]
    #     }
    #     db = self.find_one(NODES_INFO, query)
    #     if db is None:
    #         return None
    #     # get last seq in DB
    #     pipeline = [
    #         {"$match": {"node_id": node}},
    #         {"$unwind": "$energy"},
    #         {"$sort": {"energy.timestamp": -1}},
    #         {"$limit": 1},
    #         {'$project':
    #          {
    #              "_id": 1,
    #              'timestamp': '$energy.timestamp',
    #              'ewma_energy': '$energy.ewma_energy',
    #              'ewma_energy_normalized': '$energy.ewma_energy_normalized'
    #          }
    #          }
    #     ]
    #     db = self.aggregate(NODES_INFO, pipeline)
    #     for doc in db:
    #         return doc

    def get_last_delay(self, node):
        query = {
            "$and": [
                {"node_id": node},
                {"delay": {"$exists": True}}
            ]
        }
        db = self.find_one(NODES_INFO, query)
        if db is None:
            return
        # get last seq in DB
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$delay"},
            {"$sort": {"delay.timestamp": -1}},
            {"$limit": 1},
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$delay.timestamp',
                 'sampled_delay': '$delay.sampled_delay',
                 'ewma_delay': '$delay.ewma_delay',
                 'ewma_delay_normalized': '$delay.ewma_delay_normalized'
             }
             }
        ]
        db = self.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc

    def get_last_pdr(self, node):
        query = {
            "$and": [
                {"node_id": node},
                {"pdr": {"$exists": True}}
            ]
        }
        db = self.find_one(NODES_INFO, query)
        if db is None:
            return None
        # get last seq in DB
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$pdr"},
            {"$sort": {"pdr.timestamp": -1}},
            {"$limit": 1},
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$pdr.timestamp',
                 'seq': '$pdr.seq',
                 "num_seq": '$pdr.num_seq',
                 'ewma_pdr': '$pdr.ewma_pdr'
             }
             }
        ]
        db = self.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc

    def get_last_nbr_timestamp(self, node):
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$neighbors"},
            {"$group": {"_id": None, "timestamp": {"$max": "$neighbors.timestamp"}}}
        ]
        db = self.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc["timestamp"]

    def get_last_nbr(self, node):
        query = {
            "$and": [
                {"node_id": node},
                {"neighbors": {"$exists": True}}
            ]
        }
        db = self.find_one(NODES_INFO, query)
        if db is None:
            return None
        # We first need to get the last timestamp of neighbors of the given node
        timestamp = self.get_last_nbr_timestamp(node)
        # get last links
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$neighbors"},
            {"$match": {"neighbors.timestamp": timestamp}},
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$neighbors.timestamp',
                 'dst': '$neighbors.dst',
                 'rssi': '$neighbors.rssi',
                 'etx': '$neighbors.etx'
             }
             }
        ]
        db = self.aggregate(NODES_INFO, pipeline)
        return db

    def get_number_of_sensors(self):
        nbr_array = np.array(self.distinct(NODES_INFO, "neighbors.dst"))
        nodes = np.append(nbr_array, self.distinct(NODES_INFO, "node_id"))
        sensors = np.unique(nodes)
        return sensors.size

    def get_sensor_nodes(self):
        return self.find(NODES_INFO, {})

    def get_last_index_wsn(self):
        nbr_array = np.array(self.distinct(NODES_INFO, "neighbors.dst"))
        nodes = np.append(nbr_array, self.distinct(NODES_INFO, "node_id"))
        node_list = [int(elem.split('.')[0]) for elem in nodes]
        sort = np.sort(node_list)
        last = sort[-1]
        return int(last)

    def get_sensor_nodes_in_order(self):
        db = self.find(NODES_INFO, {}).sort("node_id").collation(
            Collation(locale="en_US", numericOrdering=True))
        nodes = []
        if db is None:
            return None
        for node in db:
            nodes.append(node["node_id"])
        return nodes

    """ Useful Reinforcement Learning Functions """

    def save_observations(self,
                          timestamp=None,
                          alpha=None,
                          beta=None,
                          delta=None,
                          power_wam=None,
                          power_mean=None,
                          power_normalized=None,
                          delay_wam=None,
                          delay_mean=None,
                          delay_normalized=None,
                          pdr_wam=None,
                          pdr_mean=None,
                          last_ts_in_schedule=None,
                          current_sf_len=None,
                          normalized_ts_in_schedule=None,
                          reward=None
                          ):
        data = {
            "timestamp": timestamp,
            "alpha": alpha,
            "beta": beta,
            "delta": delta,
            "power_wam": power_wam,
            "mean": power_mean,
            "power_normalized": power_normalized,
            "delay_wam": delay_wam,
            "delay_mean": delay_mean,
            "delay_normalized": delay_normalized,
            "pdr_wam": pdr_wam,
            "pdr_mean": pdr_mean,
            "last_ts_in_schedule": last_ts_in_schedule,
            "current_sf_len": current_sf_len,
            "normalized_ts_in_schedule": normalized_ts_in_schedule,
            "reward": reward
        }
        self.insert_one(OBSERVATIONS, data)

    def get_last_observations(self):
        db = self.find_one(OBSERVATIONS, {})
        if db is None:
            return None
        # get last req in DB
        db = self.find(
            OBSERVATIONS, {}).sort("_id", -1).limit(1)
        for doc in db:
            alpha = doc["alpha"]
            beta = doc["beta"]
            delta = doc["delta"]
            last_ts_in_schedule = doc['last_ts_in_schedule']
            current_sf_len = doc['current_sf_len']
            normalized_ts_in_schedule = doc['normalized_ts_in_schedule']
            reward = doc['reward']

        last_obs = {
            "alpha": alpha,
            "beta": beta,
            "delta": delta,
            "last_ts_in_schedule": last_ts_in_schedule,
            "current_sf_len": current_sf_len,
            "normalized_ts_in_schedule": normalized_ts_in_schedule,
            "reward": reward,
        }

        return last_obs

    def get_last_power_consumption(self, node, power_samples, seq):
        query = {
            "$and": [
                {"node_id": node},
                {"energy": {"$exists": True}}
            ]
        }
        db = self.find_one(NODES_INFO, query)
        if db is None:
            # FIXME: 3000 should not be set here
            power_samples.append((node, 3000))
            return
        # Get last n samples after the timestamp
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$energy"},
            {"$match": {
                "energy.cycle_seq": {
                    "$eq": seq
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
             }
             }
        ]
        db = self.aggregate(NODES_INFO, pipeline)

        energy = 0
        for doc in db:
            energy = doc['ewma_energy']
        # Calculate the avg delay
        if energy > 0:
            power_samples.append((node, energy))
        else:
            power_samples.append((node, 3000))
        return

    def get_avg_delay(self, node, delay_samples, seq):
        query = {
            "$and": [
                {"node_id": node},
                {"delay": {"$exists": True}}
            ]
        }
        db = self.find_one(NODES_INFO, query)
        if db is None:
            delay_samples.append((node, 2500))
            return
        # Get last n samples after the timestamp
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$delay"},
            {"$match": {
                "delay.cycle_seq": {
                    "$gte": seq
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

        db = self.aggregate(NODES_INFO, pipeline)

        for doc in db:
            delay = doc["sampled_delay"]
            num_rcv += 1
            sum_delay += delay

        # Calculate the avg delay
        if num_rcv > 0:
            avg_delay = sum_delay/num_rcv
        else:
            avg_delay = 2500
        delay_samples.append((node, avg_delay))
        return

    def get_avg_pdr(self, node, pdr_samples, seq):
        query = {
            "$and": [
                {"node_id": node},
                {"pdr": {"$exists": True}}
            ]
        }
        db = self.find_one(NODES_INFO, query)
        if db is None:
            pdr_samples.append((node, 0))
            return
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$pdr"},
            {"$match": {
                "pdr.cycle_seq": {
                    "$gte": seq
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
        db = self.aggregate(NODES_INFO, pipeline)
        # Variable to keep track of the number rcv packets
        num_rcv = 0
        # Last received sequence
        seq = 0
        for doc in db:
            seq = doc['seq']
            num_rcv += 1
        # Get the averaged pdr for this period
        if seq > 0:
            avg_pdr = num_rcv/seq
        else:
            avg_pdr = 0
        if avg_pdr > 1.0:
            avg_pdr = 1.0
        pdr_samples.append((node, avg_pdr))
        return
