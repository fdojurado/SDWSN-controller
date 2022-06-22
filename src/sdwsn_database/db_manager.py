from sdwsn_database.database import Database, PACKETS, NODES_INFO
from sdwsn_packet.packet import SDN_NAPL_LEN, NA_Packet_Payload
from sdwsn_packet.packet_dissector import SLOT_DURATION, SLOTFRAME_LEN
import json
from datetime import datetime
import numpy as np


class DatabaseManager(Database):
    def __init__(
        self,
        name: str = 'myDSN',
        host: str = '127.0.0.1',
        port: int = 27017
    ):
        super().__init__(name, host, port)

    def initialise_db(self):
        self.initialise()

    def save_serial_packet(self, pkt):
        # The incoming format should be JSON
        data = json.loads(pkt)
        data["timestamp"] = datetime.now().timestamp() * 1000.0
        self.insert(PACKETS, data)

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
        if(addr == "1.0"):
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

    def get_last_slotframe_len(self):
        db = self.find_one(SLOTFRAME_LEN, {})
        if db is None:
            return None
        # get last seq in DB
        db = self.find(SLOTFRAME_LEN, {}).sort("_id", -1).limit(1)
        for doc in db:
            return doc["slotframe_len"]

    def get_last_power_consumption(self, node):
        query = {
            "$and": [
                {"node_id": node},
                {"energy": {"$exists": True}}
            ]
        }
        db = self.find_one(NODES_INFO, query)
        if db is None:
            return None
        # get last seq in DB
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$energy"},
            {"$sort": {"energy.timestamp": -1}},
            {"$limit": 1},
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$energy.timestamp',
                 'ewma_energy': '$energy.ewma_energy',
                 'ewma_energy_normalized': '$energy.ewma_energy_normalized'
             }
             }
        ]
        db = self.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc

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

    def get_last_index_wsn(self):
        nbr_array = np.array(self.distinct(NODES_INFO, "neighbors.dst"))
        nodes = np.append(nbr_array, self.distinct(NODES_INFO, "node_id"))
        node_list = [int(elem.split('.')[0]) for elem in nodes]
        sort = np.sort(node_list)
        last = sort[-1]
        return int(last)
