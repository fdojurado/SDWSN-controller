# from controller.message import Message
from datetime import datetime
import struct
from controller.database.database import *
from controller.packet.packet import *
import numpy as np
import pandas as pd
from controller import globals

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
PMIN = VOLTAGE * I_LPM * 1e3  # Value in micro
PMAX = VOLTAGE * I_RX * 1.2 * 1e3  # Value in micro
MIN_TX = PMAX/3  # Max energy for the last node in the network
# Constants for packet delay calculation
SLOT_DURATION = 10
NUM_SLOTS = 17
Q_MAX = 4  # Maximum size of the queue
R_MAX = 3   # Maximum number of retransmissions
SLOTFRAME_SIZE = NUM_SLOTS * SLOT_DURATION  # Size of the dataplane slotframe

current_time = 0


def handle_serial_packet(data, ack_queue):
    global current_time
    # Get Unix timestamp from a datetime object
    current_time = datetime.now().timestamp() * 1000.0
    print("serial packet received")
    print(data)
    # Let's parse serial packet
    serial_pkt = process_serial_packet(data)
    if serial_pkt is None:
        "bad serial packet"
        return
    # Let's first save the packet
    save_serial_packet(serial_pkt)
    # Check if this is a serial ACK packet
    if serial_pkt.message_type == serial_protocol.ACK:
        ack_queue.put(serial_pkt)
        return
    # Let's now process the sdn IP packet
    pkt = process_sdn_ip_packet(serial_pkt.payload)
    # We exit processing if empty result returned
    if(not pkt):
        return
    b = int.from_bytes(b'\x0F', 'big')
    protocol = pkt.vap & b
    match protocol:
        case sdn_protocols.SDN_PROTO_NA:
            print("Processing NA packet")
            na_pkt = process_na_packet(pkt)
            if na_pkt is None:
                "bad NA packet"
                return
            # Add to number of pkts received during this period
            globals.num_packets_period += 1
            # We now build the energy DB
            save_energy(pkt, na_pkt)
            # We now build the neighbors DB
            save_neighbors(pkt, na_pkt)
            # return
        # case sdn_protocols.SDN_PROTO_NC_ROUTE:
        #     # rt_pkt = process_nc_route_packet(pkt.payload, pkt.tlen-SDN_IPH_LEN)
        #     ack_queue.put(pkt)
        #     return
        case sdn_protocols.SDN_PROTO_DATA:
            print("Processing data packet")
            data_pkt = process_data_packet(pkt)
            if data_pkt is None:
                "bad Data packet"
                return
            # Add to number of pkts received during this period
            globals.num_packets_period += 1
            # We now build the pdr DB
            save_pdr(pkt, data_pkt)
            # We now build the delay DB
            save_delay(pkt, data_pkt)
            # return
        case _:
            print("sdn IP packet type not found")
            return
    # Everytime we received a valid packet, we update the features table
    # save_features()


def process_serial_packet(data):
    # Parse sdn IP packet
    print("processing serial packet")
    pkt = SerialPacket.unpack(data)
    print(repr(pkt))
    # If the reported payload length in the serial header doesnot match the packet size,
    # then we drop the packet.
    if(len(pkt.payload) < pkt.payload_len):
        print("packet shorter than reported in serial header")
        return None
    # serial packet succeed
    print("succeed unpacking serial packet")
    return pkt


def save_serial_packet(pkt):
    data = json.loads(pkt.toJSON())
    data["timestamp"] = current_time
    Database.insert(PACKETS, data)


def process_data_packet(pkt):
    # If the reported length in the sdn IP header doesnot match the packet size,
    # then we drop the packet.
    if(len(pkt.payload) < (pkt.tlen-SDN_IPH_LEN)):
        print("Data packet shorter than reported in IP header")
        return
    # Process data packet header
    pkt = Data_Packet.unpack(pkt.payload)
    print(repr(pkt))
    # sdn IP packet succeed
    print("succeed unpacking sdn data packet")
    return pkt


def process_sdn_ip_packet(data):
    # We first check the integrity of the HEADER of the sdn IP packet
    if(sdn_ip_checksum(data, SDN_IPH_LEN) != 0xffff):
        print("bad checksum")
        return
    # Parse sdn IP packet
    print("processing IP packet")
    pkt = SDN_IP_Packet.unpack(data)
    print(repr(pkt))
    # If the reported length in the sdn IP header doesnot match the packet size,
    # then we drop the packet.
    if(len(data) < pkt.tlen):
        print("packet shorter than reported in IP header")
        return
    # sdn IP packet succeed
    print("succeed unpacking sdn IP packet")
    return pkt


def chksum(sum, data, len):
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


def sdn_ip_checksum(msg, len):
    sum = chksum(0, msg, len)
    result = 0
    if(sum == 0):
        result = 0xffff
        print("return chksum ", result)
    else:
        result = struct.pack(">i", sum)
        print("return chksum ", result)
    return result


def process_na_packet(pkt):
    length = pkt.tlen-SDN_IPH_LEN
    # We first check the integrity of the entire SDN NA packet
    if(sdn_ip_checksum(pkt.payload, length) != 0xffff):
        print("bad NA checksum")
        return
    # Parse sdn NA packet
    pkt = NA_Packet.unpack(pkt.payload, length)
    print(repr(pkt))
    # If the reported payload length in the sdn NA header does not match the packet size,
    # then we drop the packet.
    if(len(pkt.payload) < pkt.payload_len):
        print("NA packet shorter than reported in the header")
        return
    # sdn IP packet succeed
    print("succeed unpacking SDN NA packet")
    return pkt


def save_energy(pkt, na_pkt):
    # na_pkt.energy already contains the EWMA which was computed at the sensor node
    # We only need to normalize it
    # We first need to calculate the pmax_n = for this specific node which depends
    # on the rank of the node.
    h = na_pkt.rank/H_MAX
    k_n = MIN_TX/PMAX
    k_n = k_n**h
    pmax_n = PMAX * k_n
    ewma_energy_normalized = (na_pkt.energy - PMIN)/(pmax_n-PMIN)
    # historical energy
    data = {
        "timestamp": current_time,
        "ewma_energy": na_pkt.energy,
        "ewma_energy_normalized": ewma_energy_normalized,
    }
    update = {
        "$push": {
            "energy": data
        }
    }
    filter = {
        "node_id": pkt.scrStr
    }
    Database.update_one(NODES_INFO, filter, update, True, None)
    # Set the rank
    update = {
        "$set": {
            "rank": na_pkt.rank
        }
    }
    filter = {
        "node_id": pkt.scrStr
    }
    Database.update_one(NODES_INFO, filter, update, True, None)


def save_neighbors(pkt, na_pkt):
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
        Database.update_one(NODES_INFO, filter, update, True, None)


def save_pdr(pkt, data_pkt):
    # Process PDR
    # We first check if we already have knowledge of previous seq for this
    # sensor node
    query = {
        "$and": [
            {"node_id": pkt.scrStr},
            {"pdr": {"$exists": True}}
        ]
    }
    db = Database.find_one(NODES_INFO, query)
    if(db is None):
        num_seq = 1
        ewma_pdr = num_seq/data_pkt.seq
    else:
        # get last pdr
        last_pdr = get_last_pdr(pkt.scrStr)
        pdr_n_1 = last_pdr['ewma_pdr']
        num_seq = last_pdr['num_seq'] + 1
        # Compute EWMA
        pdr = num_seq/data_pkt.seq
        ewma_pdr = compute_ewma(pdr_n_1, pdr)
    data = {
        "timestamp": current_time,
        "seq": data_pkt.seq,
        "num_seq": num_seq,
        "ewma_pdr": ewma_pdr
    }
    update = {
        "$push": {
            "pdr": data
        }
    }
    filter = {
        "node_id": pkt.scrStr
    }
    Database.update_one(NODES_INFO, filter, update, True, None)


def save_delay(pkt, data_pkt):
    sampled_delay = data_pkt.asn * SLOT_DURATION
    # To calculate the min and max delay, we need to obtain the rank of the sensor node
    rank = get_rank(pkt.scrStr)
    if rank is None:
        # We have not received an NA packet yet.
        # print("we don't know the rank yet")
        rank = H_MAX
        min_delay = 1 * SLOT_DURATION
    else:
        min_delay = rank * SLOT_DURATION
    max_delay = Q_MAX * rank * R_MAX * SLOTFRAME_SIZE
    # print("rank: "+str(rank)+" min delay: "+str(min_delay)+" max delay: " +
    #       str(max_delay))
    # We now need to check whether we already have knowledge of previous delay packets
    # for this sensor node
    query = {
        "$and": [
            {"node_id": pkt.scrStr},
            {"delay": {"$exists": True}}
        ]
    }
    db = Database.find_one(NODES_INFO, query)
    if(db is None):
        ewma_delay = sampled_delay
    else:
        # get last delay
        last_delay = get_last_delay(pkt.scrStr)
        delay_n_1 = last_delay["ewma_delay"]
        # Compute EWMA
        ewma_delay = compute_ewma(delay_n_1, sampled_delay)
    # Let's normalized the delay packet
    # print("ewma delay: "+str(ewma_delay))
    ewma_delay_normalized = (ewma_delay - min_delay)/(max_delay-min_delay)
    # print("ewma delay normalized: "+str(ewma_delay_normalized))
    # Save data
    data = {
        "timestamp": current_time,
        "sampled_delay": sampled_delay,
        "ewma_delay": ewma_delay,
        "ewma_delay_normalized": ewma_delay_normalized
    }
    update = {
        "$push": {
            "delay": data
        }
    }
    filter = {
        "node_id": pkt.scrStr
    }
    Database.update_one(NODES_INFO, filter, update, True, None)


# def process_nc_route_packet(data, length):
#     print("Processing NC route packet")
#     # We first check the integrity of the HEADER of the sdn IP packet
#     if(sdn_ip_checksum(data, length) != 0xffff):
#         print("bad checksum")
#         return
#     # Parse NC route packet
#     pkt = NC_Routing_Packet.unpack(data, length)
#     print(repr(pkt))
#     # If the reported length in the sdn IP header doesnot match the packet size,
#     # then we drop the packet.
#     if(len(data) < (pkt.payload_len+SDN_NCH_LEN)):
#         print("packet shorter than reported in NC route header")
#         return
#     # sdn IP packet succeed
#     print("succeed unpacking NC route packet")
#     return pkt


# def process_nc_ack(addr, pkt):
#     pkt = NC_ACK_Packet.unpack(pkt.payload, addr)
#     print("ack received: ", pkt.ack, " from ", pkt.addrStr)
#     return pkt


# def insert_links(data):
#     links = {
#         'time': data['time'],
#         'scr': data['scr'],
#         'dst': data['dst'],
#         'rssi': data['rssi'],
#     }
#     # load the collection to pandas frame
#     db = Database.find_one("links", {}, None)
#     if(db is None):
#         Database.insert("links", links)
#     else:
#         # It first checks if the links already exists in the collection.
#         # If it does, it update with the current values, otherwise it creates it.
#         Database.push_links("links", links)


def compute_ewma(old_data, new_data):
    return (old_data * (EWMA_SCALE - EWMA_ALPHA) +
            new_data * EWMA_ALPHA) / EWMA_SCALE


def get_rank(addr):
    if(addr == "1.0"):
        return 0
    query = {
        "$and": [
            {"node_id": addr},
            {"rank": {"$exists": True}}
        ]
    }
    db = Database.find_one(NODES_INFO, query)
    if db is None:
        return
    else:
        return db["rank"]


def get_last_slotframe_len():
    db = Database.find_one(SLOTFRAME_LEN, {})
    if db is None:
        return None
    # get last seq in DB
    db = Database.find(SLOTFRAME_LEN, {}).sort("_id", -1).limit(1)
    for doc in db:
        return doc["slotframe_len"]


def get_last_power_consumption(node):
    query = {
        "$and": [
            {"node_id": node},
            {"energy": {"$exists": True}}
        ]
    }
    db = Database.find_one(NODES_INFO, query)
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
    db = Database.aggregate(NODES_INFO, pipeline)
    for doc in db:
        return doc


def get_last_delay(node):
    query = {
        "$and": [
            {"node_id": node},
            {"delay": {"$exists": True}}
        ]
    }
    db = Database.find_one(NODES_INFO, query)
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
    db = Database.aggregate(NODES_INFO, pipeline)
    for doc in db:
        return doc


def get_last_pdr(node):
    query = {
        "$and": [
            {"node_id": node},
            {"pdr": {"$exists": True}}
        ]
    }
    db = Database.find_one(NODES_INFO, query)
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
    db = Database.aggregate(NODES_INFO, pipeline)
    for doc in db:
        return doc


def get_last_nbr_timestamp(node):
    pipeline = [
        {"$match": {"node_id": node}},
        {"$unwind": "$neighbors"},
        {"$group": {"_id": None, "timestamp": {"$max": "$neighbors.timestamp"}}}
    ]
    db = Database.aggregate(NODES_INFO, pipeline)
    for doc in db:
        return doc["timestamp"]


def get_last_nbr(node):
    query = {
        "$and": [
            {"node_id": node},
            {"neighbors": {"$exists": True}}
        ]
    }
    db = Database.find_one(NODES_INFO, query)
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
    db = Database.aggregate(NODES_INFO, pipeline)
    return db


def get_last_index_wsn():
    nbr_array = np.array(Database.distinct(NODES_INFO, "neighbors.dst"))
    nodes = np.append(nbr_array, Database.distinct(NODES_INFO, "node_id"))
    node_list = [int(elem.split('.')[0]) for elem in nodes]
    sort = np.sort(node_list)
    last = sort[-1]
    return int(last)


def save_features():
    # Get last index of sensor
    N = get_last_index_wsn()+1
    # Neighbor matrix
    globals.nbr_rssi_matrix = np.zeros(shape=(N, N))
    globals.nbr_etx_matrix = np.zeros(shape=(N, N))
    # Get user requirements
    alpha = 0.5
    beta = 0.5
    delta = 0.5
    user_requirements = np.array([alpha, beta, delta])
    # Get average power consumption, delay, and pdr normalized
    overall_power_consuption = 0
    overall_delay = 0
    overall_pdr = 0
    energy_number_of_sensor_nodes = 0
    delay_number_of_sensor_nodes = 0
    pdr_number_of_sensor_nodes = 0
    # We first loop through all sensor nodes
    nodes = Database.find(NODES_INFO, {})
    for node in nodes:
        # Get the energy consumption for this particular sensor node
        energy = get_last_power_consumption(node["node_id"])
        # Get the delay normalized
        delay = get_last_delay(node["node_id"])
        # Get the last pdr
        pdr = get_last_pdr(node["node_id"])
        # Get last neighbors
        nbr = get_last_nbr(node["node_id"])
        if energy is not None:
            energy_number_of_sensor_nodes += 1
            overall_power_consuption += energy["ewma_energy_normalized"]
        if delay is not None:
            delay_number_of_sensor_nodes += 1
            overall_delay += delay["ewma_delay_normalized"]
        if pdr is not None:
            pdr_number_of_sensor_nodes += 1
            overall_pdr += pdr["ewma_pdr"]
        if nbr is not None:
            for nbr_node in nbr:
                source, zero = node["node_id"].split('.')
                dst, zero = nbr_node["dst"].split('.')
                globals.nbr_rssi_matrix[int(source)][int(
                    dst)] = int(nbr_node["rssi"])
                globals.nbr_etx_matrix[int(source)][int(
                    dst)] = int(nbr_node["etx"])
    if(energy_number_of_sensor_nodes > 0):
        wsn_energy_normalized = overall_power_consuption/energy_number_of_sensor_nodes
    else:
        wsn_energy_normalized = None
    if(delay_number_of_sensor_nodes > 0):
        wsn_delay_normalized = overall_delay/delay_number_of_sensor_nodes
    else:
        wsn_delay_normalized = None
    if(pdr_number_of_sensor_nodes > 0):
        wsn_reliability_normalized = overall_pdr/pdr_number_of_sensor_nodes
    else:
        wsn_reliability_normalized = None
    # Flatten RSSI and ETX matrices
    rssi_neighbors = globals.nbr_rssi_matrix.flatten().tolist()
    etx_neighbors = globals.nbr_etx_matrix.flatten().tolist()
    # Calculation of the optimization equation
    if(wsn_energy_normalized is not None and wsn_delay_normalized is not None and wsn_reliability_normalized is not None):
        calculation_optimization_eq = alpha*wsn_energy_normalized + \
            beta*wsn_delay_normalized-delta*wsn_reliability_normalized
    else:
        calculation_optimization_eq = None
    # We now get the latest running routing path from the ROUTING_PATHS collection
    if(globals.routes_matrix.size == 0):
        routing_paths = None
    else:
        routing_paths = globals.routes_matrix.flatten().tolist()
    # Get the slotframe size
    last = get_last_slotframe_len()
    if(last is None):
        slotframe_len = None
    else:
        slotframe_len = last
    # Get the tsch schedules for this round
    if not globals.link_schedules_matrices:
        tsch_schedules = None
    else:
        tsch_schedules = globals.link_schedules_matrices
    # Elapse time since the last RA and SA packet sent
    if globals.elapse_time == 0:
        elapsetime = None
    else:
        elapsetime = current_time - globals.elapse_time
    # Save data
    data = {
        "timestamp": current_time,
        "elapsetime": elapsetime,
        "user_requirements": user_requirements.tolist(),
        "wsn_energy_normalized": wsn_energy_normalized,
        "wsn_delay_normalized": wsn_delay_normalized,
        "wsn_reliability_normalized": wsn_reliability_normalized,
        "routing_paths": routing_paths,
        "slotframe_len": slotframe_len,
        "tsch_schedules": tsch_schedules,
        "rssi_neighbors": rssi_neighbors,
        "etx_neighbors": etx_neighbors,
        "calculation_optimization_eq": calculation_optimization_eq
    }
    Database.insert(FEATURES, data)
