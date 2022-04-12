# from controller.message import Message
from datetime import datetime
import struct
from controller.database.database import Database
from controller.packet.packet import *
import pandas as pd

current_time = 0


def handle_serial_packet(data, ack_queue):
    print("serial packet received")
    print(data)
    # Let's parse serial packet
    serial_pkt = process_serial_packet(data)
    if serial_pkt is None:
        "bad serial packet"
        return
    # Let's firt validate the packet
    save_serial_packet(serial_pkt)
    # Let's first process the sdn IP packet
    pkt = process_sdn_ip_packet(serial_pkt.payload)
    # We exit processing if empty result returned
    if(not pkt):
        return
    b = int.from_bytes(b'\x0F', 'big')
    protocol = pkt.vap & b
    match protocol:
        case sdn_protocols.SDN_PROTO_NA:
            print("Processing NA packet")
            na_pkt = process_na_packet(
                pkt.scr, pkt.payload, pkt.tlen-SDN_IPH_LEN)
            if(not na_pkt):
                return
            process_na_payload(pkt.scr, na_pkt.payload)
            return
        case sdn_protocols.SDN_PROTO_NC_ROUTE:
            # rt_pkt = process_nc_route_packet(pkt.payload, pkt.tlen-SDN_IPH_LEN)
            ack_queue.put(pkt)
            return
        case sdn_protocols.SDN_PROTO_DATA:
            print("Processing data packet")
            process_data_packet(pkt.payload)
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
    global current_time
    # Get Unix timestamp from a datetime object
    current_time = datetime.now().timestamp() * 1000.0
    data = {
        "ts": current_time,
        "values": {
            "addr": pkt.addr,
            "type": pkt.message_type,
            "payload_len": pkt.payload_len,
            "reserved0": pkt.reserved0,
            "reserved1": pkt.reserved1,
            "payload": pkt.payload
        }
    }
    Database.insert("packets", data)


def process_data_packet(data):
    # Process data packet header
    pkt_hdr = DataPacketHeader.unpack(data)
    print(repr(pkt_hdr))
    blocks = pkt_hdr.length // SDN_DATA_LEN
    payload = pkt_hdr.payload
    payload_size = pkt_hdr.length
    for x in range(1, blocks+1):
        payload_size = payload_size - SDN_DATA_LEN
        print("remaining payload size: ", payload_size)
        data_pkt = DataPacketPayload.unpack(payload, payload_size)
        print(repr(data_pkt))
        payload = data_pkt.payload
        src = data_pkt.addrStr
        data = {
            'time': current_time,
            'src': src,
            'last_seq': data_pkt.seq,
            'num_seq': 1,
            'temp': data_pkt.temp,
            'humidity': data_pkt.humidity,
        }
        node = {
            '_id': src,
            'data': [
                data,
            ]
        }
        """ Does this node exist in DB """
        if Database.exist("nodes", src) == 0:
            Database.insert("nodes", node)
        else:
            # look for last seq number for that node
            db = Database.find_one("nodes", {"data.src": src}, None)
            if(db is not None):
                df = pd.DataFrame(db['data'])
                df = df.tail(1)
                if df['last_seq'].values[0] == data_pkt.seq:
                    print("duplicated data packet")
                    # update num_seq field with the one in DB
                    data['num_seq'] = int(df['num_seq'].values[0])
                else:
                    data['num_seq'] = int(df['num_seq'].values[0]+1)
                    Database.push_doc("nodes", src, 'data', data)
            else:
                Database.push_doc("nodes", src, 'data', data)
        """ Create a current PDR database """
        pdr = data['num_seq'] * 100.0 / data['last_seq']
        pdr_data = {
            '_id': src,
            'time': current_time,
            'pdr': pdr,
        }
        if Database.exist("pdr", src) == 0:
            Database.insert("pdr", pdr_data)
        else:
            Database.update_pdr("pdr", src, pdr_data)
        ''' after we finish updating the pdr field, we
            want to create/update pdr text so the canvas can
            be updated '''
        coll = Database.find("pdr", {})
        df = pd.DataFrame(coll)
        mean = df.pdr.mean()
        data = {
            "ts": current_time,
            "pdr": mean,
        }
        Database.insert("total_pdr", data)


def process_sdn_ip_packet(data):
    # We first check the entegrity of the HEADER of the sdn IP packet
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


def process_na_packet(addr, data, length):
    addr = addrConversion.to_string(addr)
    addr = addr.addrStr
    # We first check the entegrity of the HEADER of the sdn IP packet
    if(sdn_ip_checksum(data, length) != 0xffff):
        print("bad checksum")
        return
    # Parse sdn IP packet
    pkt = NA_Packet.unpack(data, length)
    print(repr(pkt))
    # If the reported length in the sdn IP header doesnot match the packet size,
    # then we drop the packet.
    if(len(data) < (pkt.payload_len+SDN_NAH_LEN)):
        print("packet shorter than reported in NA header")
        return
    # sdn IP packet succeed
    print("succeed unpacking SDN NA packet")
    """ Now, we want to process node information embedded in the NA packet """
    nodes = Database.find("nodes", {})
    # Total number of NB
    num_nb = 0
    for node in nodes:
        if node['_id'] == addr:
            df = pd.DataFrame(node['nbr'])
            num_nb = df.dst.nunique()
    data = {
        'time': current_time,
        'energy': pkt.energy,
        'rank': pkt.rank,
        'total_nb': num_nb
    }
    node = {
        '_id': addr,
        'info': [
            data
        ]
    }
    if Database.exist("nodes", addr) == 0:
        Database.insert("nodes", node)
    else:
        Database.push_doc("nodes", addr, 'info', data)
    """ Create a current energy database """
    data = {
        '_id': addr,
        'time': current_time,
        'energy': pkt.energy,
    }
    if Database.exist("energy", addr) == 0:
        Database.insert("energy", data)
    else:
        print('updating energy')
        Database.update_energy("energy", addr, data)
    ''' after we finish updating the energy field, we
     want to create/update energy text so the canvas can be updated '''
    coll = Database.find("energy", {})
    df = pd.DataFrame(coll)
    summation = df.energy.sum()
    data = {
        "ts": current_time,
        "energy": int(summation),
    }
    Database.insert("total_energy", data)
    return pkt


def process_na_payload(addr, data):
    addr = addrConversion.to_string(addr).addrStr
    # """ Let's process NA payload """
    # Process neighbours
    blocks = len(data) // SDN_NAPL_LEN
    idx_start = 0
    idx_end = 0
    for x in range(1, blocks+1):
        idx_end += SDN_NAPL_LEN
        payload = data[idx_start:idx_end]
        idx_start = idx_end
        payload_unpacked = NA_Packet_Payload.unpack(payload)
        data_structure = {
            'time': current_time,
            'scr': addr,
            'dst': payload_unpacked.addrStr,
            'rssi': payload_unpacked.rssi,
            'etx': payload_unpacked.etx,
        }
        node = {
            '_id': addr,
            'nbr': [
                data_structure,
            ]
        }
        if Database.exist("nodes", addr) == 0:
            Database.insert("nodes", node)
        else:
            Database.push_doc("nodes", addr, 'nbr', data_structure)
        #  Insert entry to the current links table
        insert_links(data_structure)


def process_nc_route_packet(data, length):
    print("Processing NC route packet")
    # We first check the entegrity of the HEADER of the sdn IP packet
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
