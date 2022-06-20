from datetime import datetime

import struct

from sdwsn_database.database import Database, PACKETS, NODES_INFO, FEATURES, SLOTFRAME_LEN

from sdwsn_packet.packet import serial_protocol, sdn_protocols
from sdwsn_packet.packet import SerialPacket, SDN_IP_Packet
from sdwsn_packet.packet import Data_Packet, NA_Packet, NA_Packet_Payload
from sdwsn_packet.packet import SDN_IPH_LEN, SDN_NAPL_LEN

from sdwsn_common import globals

import json

import numpy as np
import pandas as pd

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

current_time = 0


class PacketDissector():
    def __init__(self, name, database, ack=None, cycle_sequence=0, sequence=0) -> None:
        self.name = name
        self.db = database
        self.ack_queue = ack
        self.cycle_sequence = cycle_sequence
        self.sequence = sequence

    def handle_serial_packet(self, data):
        global current_time
        # Get Unix timestamp from a datetime object
        current_time = datetime.now().timestamp() * 1000.0
        print("serial packet received")
        print(data)
        # Let's parse serial packet
        serial_pkt = self.process_serial_packet(data)
        if serial_pkt is None:
            print("bad serial packet")
            return
        # Let's first save the packet
        self.save_serial_packet(serial_pkt)
        # Check if this is a serial ACK packet
        if serial_pkt.message_type == serial_protocol.ACK:
            self.ack_queue.put(serial_pkt)
            return
        # Let's now process the sdn IP packet
        pkt = self.process_sdn_ip_packet(serial_pkt.payload)
        # We exit processing if empty result returned
        if(not pkt):
            return
        b = int.from_bytes(b'\x0F', 'big')
        protocol = pkt.vap & b
        match protocol:
            case sdn_protocols.SDN_PROTO_NA:
                # print("Processing NA packet")
                na_pkt = self.process_na_packet(pkt)
                if na_pkt is None:
                    print("bad NA packet")
                    return
                # Add to number of pkts received during this period
                if not na_pkt.cycle_seq == self.cycle_sequence:
                    return
                print(repr(pkt))
                print(repr(na_pkt))
                self.sequence += 1
                print(f"num seq (NA): {self.sequence}")
                # We now build the energy DB
                self.save_energy(pkt, na_pkt)
                # We now build the neighbors DB
                self.save_neighbors(pkt, na_pkt)
                return
            case sdn_protocols.SDN_PROTO_DATA:
                # print("Processing data packet")
                data_pkt = self.process_data_packet(pkt)
                if data_pkt is None:
                    print("bad Data packet")
                    return
                # Add to number of pkts received during this period
                if not data_pkt.cycle_seq == self.cycle_sequence:
                    return
                print(repr(pkt))
                print(repr(data_pkt))
                self.sequence += 1
                print(f"num seq (data): {self.sequence}")
                # We now build the pdr DB
                self.save_pdr(pkt, data_pkt)
                # We now build the delay DB
                self.save_delay(pkt, data_pkt)
                return
            case _:
                print("sdn IP packet type not found")
                return

    def process_serial_packet(self, data):
        # Parse sdn IP packet
        # print("processing serial packet")
        pkt = SerialPacket.unpack(data)
        # print(repr(pkt))
        # If the reported payload length in the serial header doesn't match the packet size,
        # then we drop the packet.
        if(len(pkt.payload) < pkt.payload_len):
            print("packet shorter than reported in serial header")
            return None
        # serial packet succeed
        # print("succeed unpacking serial packet")
        return pkt

    def save_serial_packet(self, pkt):
        data = json.loads(pkt.toJSON())
        data["timestamp"] = current_time
        self.db.insert(PACKETS, data)

    def process_data_packet(self, pkt):
        # If the reported length in the sdn IP header doesn't match the packet size,
        # then we drop the packet.
        if(len(pkt.payload) < (pkt.tlen-SDN_IPH_LEN)):
            print("Data packet shorter than reported in IP header")
            return
        # Process data packet header
        pkt = Data_Packet.unpack(pkt.payload)
        # print(repr(pkt))
        # sdn IP packet succeed
        # print("succeed unpacking sdn data packet")
        return pkt

    def process_sdn_ip_packet(self, data):
        # We first check the integrity of the HEADER of the sdn IP packet
        if(self.sdn_ip_checksum(data, SDN_IPH_LEN) != 0xffff):
            print("bad checksum")
            return
        # Parse sdn IP packet
        # print("processing IP packet")
        pkt = SDN_IP_Packet.unpack(data)
        # print(repr(pkt))
        # If the reported length in the sdn IP header doesn't match the packet size,
        # then we drop the packet.
        if(len(data) < pkt.tlen):
            print("packet shorter than reported in IP header")
            return
        # sdn IP packet succeed
        # print("succeed unpacking sdn IP packet")
        return pkt

    def chksum(self, sum, data, len):
        total = sum
        # Add up 16-bit words
        num_words = len // 2
        for chunk in struct.unpack("!%sH" % num_words, data[0:num_words * 2]):
            total += chunk
        # Add any left over byte
        if len % 2:
            total += data[-1] << 8
        # Fold 32-bits into 16-bits
        total = (total >> 16) + (total & 0xffff)
        total += total >> 16
        return ~total + 0x10000 & 0xffff

    def sdn_ip_checksum(self, msg, len):
        sum = self.chksum(0, msg, len)
        result = 0
        if(sum == 0):
            result = 0xffff
            # print("return chksum ", result)
        else:
            result = struct.pack(">i", sum)
            # print("return chksum ", result)
        return result

    def process_na_packet(self, pkt):
        length = pkt.tlen-SDN_IPH_LEN
        # We first check the integrity of the entire SDN NA packet
        if(self.sdn_ip_checksum(pkt.payload, length) != 0xffff):
            print("bad NA checksum")
            return
        # Parse sdn NA packet
        pkt = NA_Packet.unpack(pkt.payload, length)
        # print(repr(pkt))
        # If the reported payload length in the sdn NA header does not match the packet size,
        # then we drop the packet.
        if(len(pkt.payload) < pkt.payload_len):
            print("NA packet shorter than reported in the header")
            return
        # sdn IP packet succeed
        # print("succeed unpacking SDN NA packet")
        return pkt

    def save_energy(self, pkt, na_pkt):
        data = {
            "timestamp": current_time,
            "cycle_seq": na_pkt.cycle_seq,
            "seq": na_pkt.seq,
            "ewma_energy": na_pkt.energy
            # "ewma_energy_normalized": ewma_energy_normalized,
        }
        update = {
            "$push": {
                "energy": data
            }
        }
        filter = {
            "node_id": pkt.scrStr
        }
        self.db.update_one(NODES_INFO, filter, update, True, None)
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
        self.db.update_one(NODES_INFO, filter, update, True, None)
        # Database.update_one(NODES_INFO, filter, update, True, None)

    def save_neighbors(self, pkt, na_pkt):
        # """ Let's process NA payload """
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
            self.db.update_one(NODES_INFO, filter, update, True, None)
            # Database.update_one(NODES_INFO, filter, update, True, None)

    def save_pdr(self, pkt, data_pkt):
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
        self.db.update_one(NODES_INFO, filter, update, True, None)
        # Database.update_one(NODES_INFO, filter, update, True, None)

    def save_delay(self, pkt, data_pkt):
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
        self.db.update_one(NODES_INFO, filter, update, True, None)
        # Database.update_one(NODES_INFO, filter, update, True, None)

    def compute_ewma(self, old_data, new_data):
        return (old_data * (EWMA_SCALE - EWMA_ALPHA) +
                new_data * EWMA_ALPHA) / EWMA_SCALE

    def get_rank(self, addr):
        if(addr == "1.0"):
            return 0
        query = {
            "$and": [
                {"node_id": addr},
                {"rank": {"$exists": True}}
            ]
        }
        db = self.db.find_one(NODES_INFO, query)
        # db = Database.find_one(NODES_INFO, query)
        if db is None:
            return
        else:
            return db["rank"]

    def get_last_slotframe_len(self):
        db = self.db.find_one(SLOTFRAME_LEN, {})
        # db = Database.find_one(SLOTFRAME_LEN, {})
        if db is None:
            return None
        # get last seq in DB
        db = self.db.find(SLOTFRAME_LEN, {}).sort("_id", -1).limit(1)
        # db = Database.find(SLOTFRAME_LEN, {}).sort("_id", -1).limit(1)
        for doc in db:
            return doc["slotframe_len"]

    def get_last_power_consumption(self, node):
        query = {
            "$and": [
                {"node_id": node},
                {"energy": {"$exists": True}}
            ]
        }
        db = self.db.find_one(NODES_INFO, query)
        # db = Database.find_one(NODES_INFO, query)
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
        db = self.db.aggregate(NODES_INFO, pipeline)
        # db = Database.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc

    def get_last_delay(self, node):
        query = {
            "$and": [
                {"node_id": node},
                {"delay": {"$exists": True}}
            ]
        }
        db = self.db.find_one(NODES_INFO, query)
        # db = Database.find_one(NODES_INFO, query)
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
        db = self.db.aggregate(NODES_INFO, pipeline)
        # db = Database.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc

    def get_last_pdr(self, node):
        query = {
            "$and": [
                {"node_id": node},
                {"pdr": {"$exists": True}}
            ]
        }
        db = self.db.find_one(NODES_INFO, query)
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
        db = self.db.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc

    def get_last_nbr_timestamp(self, node):
        pipeline = [
            {"$match": {"node_id": node}},
            {"$unwind": "$neighbors"},
            {"$group": {"_id": None, "timestamp": {"$max": "$neighbors.timestamp"}}}
        ]
        db = self.db.aggregate(NODES_INFO, pipeline)
        for doc in db:
            return doc["timestamp"]

    def get_last_nbr(self, node):
        query = {
            "$and": [
                {"node_id": node},
                {"neighbors": {"$exists": True}}
            ]
        }
        db = self.db.find_one(NODES_INFO, query)
        if db is None:
            return None
        # We first need to get the last timestamp of neighbors of the given node
        timestamp = get_last_nbr_timestamp(node)
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
        db = self.db.aggregate(NODES_INFO, pipeline)
        return db

    def get_number_of_sensors(self):
        nbr_array = np.array(self.db.distinct(NODES_INFO, "neighbors.dst"))
        nodes = np.append(nbr_array, self.db.distinct(NODES_INFO, "node_id"))
        sensors = np.unique(nodes)
        return sensors.size

    def get_last_index_wsn(self):
        nbr_array = np.array(self.db.distinct(NODES_INFO, "neighbors.dst"))
        nodes = np.append(nbr_array, self.db.distinct(NODES_INFO, "node_id"))
        node_list = [int(elem.split('.')[0]) for elem in nodes]
        sort = np.sort(node_list)
        last = sort[-1]
        return int(last)
