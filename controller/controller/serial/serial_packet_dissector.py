# from controller.message import Message
from datetime import datetime
import struct
from controller.database.database import Database
from controller.packet.packet import *
import pandas as pd

current_time = 0


def handle_serial_packet(msg):
    print("serial packet received")
    msg.print_packet()
    # Let's firt validate the packet
    save_serial_packet(msg)
    # Let's first process the sdn IP packet
    pkt = process_sdn_ip_packet(msg)
    # We exit processing if empty result returned
    if(not pkt):
        return
    match pkt.proto:
        case sdn_protocols.SDN_PROTO_NA:
            print("Processing control packet")
            process_control_packet(pkt.payload)
            return
        case sdn_protocols.SDN_PROTO_DATA:
            print("Processing data packet")
            process_data_packet(msg)
            return
        case _:
            print("message type not found")
            return


def save_serial_packet(msg):
    global current_time
    # Get Unix timestamp from a datetime object
    current_time = datetime.now().timestamp() * 1000.0
    msg.print_packet()
    addr0 = str(msg.addr0)
    addr1 = str(msg.addr1)
    addr = addr0+'.'+addr1
    hex_data = bytes(msg.data).hex()
    data = {
        "ts": current_time,
        "values": {
            "addr": addr,
            "type": msg.message_type,
            "payload_len": msg.payload_len,
            "reserved0": msg.reserved0,
            "reserved1": msg.reserved1,
            "payload": hex_data
        }
    }
    Database.insert("packets", data)


def process_data_packet(msg):
    # Source address
    addr0 = str(msg.addr0)
    addr1 = str(msg.addr1)
    addr = addr0+'.'+addr1
    # Parse header of data packet
    hdr = msg.data[:DATA_PKT_HEADER_SIZE]
    payload_len = int.from_bytes(hdr, "big")
    # Parse payload of data packet
    payload = msg.data[DATA_PKT_HEADER_SIZE:]
    blocks = payload_len // DATA_PKT_PAYLOAD_SIZE
    for x in range(1, blocks+1):
        sliced_data = payload[(-1+x)*8:x*8]
        addr0, addr1, seq, temp, humidity = struct.unpack(
            '!bbHHH', sliced_data)
        src = str(addr1)+'.'+str(addr0)
        data = {
            'time': current_time,
            'src': src,
            'last_seq': seq,
            'num_seq': 1,
            'temp': temp,
            'humidity': humidity,
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
            db = Database.find_one("nodes", {"data.src": src})
            if(db is not None):
                df = pd.DataFrame(db['data'])
                df = df.tail(1)
                if df['last_seq'].values[0] == seq:
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


def process_control_packet(data):
    # Parse control packet
    print("processing control packet")
    pkt = ControlPacket.unpack(data)
    # We first check the entegrity of the control packet
    if(sdn_cp_checksum(data, pkt.length+CP_PKT_HEADER_SIZE) != 0xffff):
        print("bad checksum")
        return
    # If the reported length in the cp header doesnot match the packet size,
    # then we drop the packet.
    if(len(data) < (pkt.length+CP_PKT_HEADER_SIZE)):
        print("packet shorter than reported in CP header")
        return
    # Type of control packet
    match pkt.type:
        case sdn_protocols.SDN_PROTO_NA :
            # NA packet
            print("NA processing")
            process_na_packet(addr, rank, energy, payload, payload_len)
            return
        case _:
            # Default
            print("control packet type not found")


def process_sdn_ip_packet(msg):
    # We first check the entegrity of the HEADER of the sdn IP packet
    if(sdn_ip_checksum(msg.data, IP_PKT_HEADER_SIZE) != 0xffff):
        print("bad checksum")
        return
    # Parse sdn IP packet
    print("processing IP packet")
    pkt = SDN_IP_Packet.unpack(msg.data)
    print(repr(pkt))
    # If the reported length in the sdn IP header doesnot match the packet size,
    # then we drop the packet.
    if(len(msg.data) < pkt.length):
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
        print("return chksum ", ord(result))
    return result


def sdn_cp_checksum(msg, len):
    sum = chksum(0, msg, len)
    result = 0
    if(sum == 0):
        result = 0xffff
        print("return chksum ", result)
    else:
        result = struct.pack(">i", sum)
        print("return chksum ", ord(result))
    return result


def process_na_packet(addr, node_rank, energy, payload, len):
    """ Let's process neighbour advertisement packets """
    # Process neighbours
    blocks = len // 6
    for x in range(1, blocks+1):
        sliced_data = payload[(-1+x)*6:x*6]
        addr0, addr1, rssi, rank = struct.unpack('!bbhh', sliced_data)
        dst = str(addr1)+'.'+str(addr0)
        data = {
            'time': current_time,
            'scr': addr,
            'dst': dst,
            'rssi': rssi,
            'rank': rank,
        }
        node = {
            '_id': addr,
            'nbr': [
                data,
            ]
        }
        if Database.exist("nodes", addr) == 0:
            Database.insert("nodes", node)
        else:
            Database.push_doc("nodes", addr, 'nbr', data)
        #  Insert entry to the current links table
        insert_links(data)
    """ Now, we want to process node information embedded in the CP packet """
    nodes = Database.find("nodes", {})
    # Total number of NB
    num_nb = 0
    for node in nodes:
        if node['_id'] == addr:
            df = pd.DataFrame(node['nbr'])
            num_nb = df.dst.nunique()
    data = {
        'time': current_time,
        'energy': energy,
        'rank': node_rank,
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
        'energy': energy,
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


def insert_links(data):
    links = {
        'time': data['time'],
        'scr': data['scr'],
        'dst': data['dst'],
        'rssi': data['rssi'],
    }
    # load the collection to pandas frame
    db = Database.find_one("links", {})
    if(db is None):
        Database.insert("links", links)
    else:
        # It first checks if the links already exists in the collection.
        # If it does, it update with the current values, otherwise it creates it.
        Database.push_links("links", links)
