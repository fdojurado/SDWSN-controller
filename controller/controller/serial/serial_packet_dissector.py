# from controller.message import Message
from datetime import datetime
import struct
from controller.database.database import *
from controller.packet.packet import *
import pandas as pd

# Network parameters
H_MAX = 10  # max number of hops
#  EWMA (exponential moving average) used to maintain statistics over time
EWMA_SCALE = 100
EWMA_ALPHA = 40
# Sensor nodes electrical parameters references
VOLTAGE = 3
I_LPM = 0.545  # mA
I_TX = 17.4  # mA
# Constants for energy normalization
ENERGY_SAMPLE_DURATION = 10  # seconds
EMIN = VOLTAGE * ENERGY_SAMPLE_DURATION * I_LPM
EMAX = VOLTAGE * ENERGY_SAMPLE_DURATION * I_TX

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
            # We now build the energy DB
            save_energy(pkt, na_pkt)
            # We now build the neighbors DB
            save_neighbors(pkt, na_pkt)
            return
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
            # We now build the pdr DB
            save_pdr(pkt, data_pkt)
            return
        case _:
            print("sdn IP packet type not found")
            return


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
    # We first need to calculate the emax_n = for this specific node which depends
    # on the rank of the node.
    h = na_pkt.rank/H_MAX
    k = (EMAX-EMIN)/5
    k_n = k/EMAX
    k_n = k_n**h
    emax_n = EMAX * k_n
    ewma_energy_normalized = (na_pkt.energy - EMIN)/(emax_n-EMIN)
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
        # get last seq in DB
        pipeline = [
            {"$match": {"node_id": pkt.scrStr}},
            {"$unwind": "$pdr"},
            {"$sort": {"pdr.timestamp": -1}},
            {"$limit": 1},
            {'$project':
             {
                 "_id": 1,
                 'timestamp': '$pdr.timestamp',
                 'seq': '$pdr.seq',
                 'num_seq': '$pdr.num_seq',
                 'ewma_pdr': '$pdr.ewma_pdr'
             }
             }
        ]
        db = Database.aggregate(NODES_INFO, pipeline)
        for doc in db:
            pdr_n_1 = doc['ewma_pdr']
            num_seq = doc['num_seq'] + 1
        # Compute EWMA
        pdr = num_seq/data_pkt.seq
        ewma_pdr = (pdr_n_1 * (EWMA_SCALE - EWMA_ALPHA) +
                    pdr * EWMA_ALPHA) / EWMA_SCALE
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


def process_nc_route_packet(data, length):
    print("Processing NC route packet")
    # We first check the integrity of the HEADER of the sdn IP packet
    if(sdn_ip_checksum(data, length) != 0xffff):
        print("bad checksum")
        return
    # Parse NC route packet
    pkt = NC_Routing_Packet.unpack(data, length)
    print(repr(pkt))
    # If the reported length in the sdn IP header doesnot match the packet size,
    # then we drop the packet.
    if(len(data) < (pkt.payload_len+SDN_NCH_LEN)):
        print("packet shorter than reported in NC route header")
        return
    # sdn IP packet succeed
    print("succeed unpacking NC route packet")
    return pkt


def process_nc_ack(addr, pkt):
    pkt = NC_ACK_Packet.unpack(pkt.payload, addr)
    print("ack received: ", pkt.ack, " from ", pkt.addrStr)
    return pkt


def insert_links(data):
    links = {
        'time': data['time'],
        'scr': data['scr'],
        'dst': data['dst'],
        'rssi': data['rssi'],
    }
    # load the collection to pandas frame
    db = Database.find_one("links", {}, None)
    if(db is None):
        Database.insert("links", links)
    else:
        # It first checks if the links already exists in the collection.
        # If it does, it update with the current values, otherwise it creates it.
        Database.push_links("links", links)
