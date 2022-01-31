import socket
import sys

from controller import Message
from typing import Optional, Union, Iterator, Tuple
from time import time
from datetime import datetime
from time import mktime
import struct
import threading
from datetime import datetime
from controller.database.database import Database
from controller.mqtt.mqtt import MQTTClient
import pandas as pd
import struct
import json

try:
    import serial
except ImportError:
    logger.warning(
        "You won't be able to use the serial can backend without "
        "the serial module installed!"
    )
    serial = None

try:
    from serial.tools import list_ports
except ImportError:
    list_ports = None


PACKET = '/serial/packet'
ENERGY = '/serial/na/energy'
PDR = '/serial/data/pdr'
current_time = 0


class SerialBus(MQTTClient):

    def on_connect(self, client, userdata, flags, result_code):
        """Callback that is called when the serial interface connects to the MQTT
        broker."""
        super().on_connect(client, userdata, flags, result_code)
        # Create a TCP/IP socket
        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect the socket to the port where the server is listening
        server_address = (self.config.serial.host, self.config.serial.port)
        print('connecting to %s port %s' % server_address)
        result = self.ser.connect_ex(server_address)
        if result:
            return 0
        else:
            t1 = threading.Thread(target=self.get_data)
            t1.daemon = True
            t1.start()
            return 1

    def process_cp(self, msg):
        # Source address
        addr0 = str(msg.addr0)
        addr1 = str(msg.addr1)
        addr = addr0+'.'+addr1
        # Parse header of control packet
        cp_hdr = msg.data[:10]  # 10 is the header size
        cp_type, cp_len, cp_rank, cp_energy, cp_rt_chksum, cp_nachksum = struct.unpack(
            '!BBhhhh', cp_hdr)
        # Parse payload of control packet
        cp_payload = msg.data[10:]  # 10 is the header size
        # Type of control packet
        print('control packet from')
        print(addr)
        print('control packet type')
        print(cp_type)
        print('control packet len')
        print(cp_len)
        print('control packet rank')
        print(cp_rank)
        print('control packet energy')
        print(cp_energy)
        print('control packet routing checksum')
        print(cp_rt_chksum)
        print('control packet routing nachksum')
        print(cp_nachksum)

        if cp_type == 3:
            print('NA received')
            self.process_neighbours(addr, cp_len, cp_payload)
            self.process_nodes(addr, cp_energy, cp_rank, cp_payload)
            msg2 = Message(
                addr0=2,
                addr1=0,
                message_type=2,
                payload_len=msg.payload_len,
                reserved0=0,
                reserved1=0,
                data=msg.data,
            )
            self.send(msg2)

    def process_data_packet(self, msg):
        # Source address
        addr0 = str(msg.addr0)
        addr1 = str(msg.addr1)
        addr = addr0+'.'+addr1
        # Parse header of data packet
        dp_hdr = msg.data[:1]  # 1 is the header size
        data_payload_len = int.from_bytes(dp_hdr, "big")
        # Parse payload of data packet
        dp_payload = msg.data[1:]  # 10 is the header size
        data = {}
        node = {}
        """ Process data packet payload """
        blocks = int(data_payload_len/8)  # 8 is the size of a data packet
        for x in range(1, blocks+1):
            sliced_data = dp_payload[(-1+x)*8:x*8]
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
            print('printing data packet')
            print(node)
            """ Does this node exist in DB """
            if Database.exist("nodes", src) == 0:
                Database.insert("nodes", node)
            else:
                # look for last seq number for that node
                data_db = Database.find_one("nodes", {"data.src": src})
                print('data_db')
                print(data_db)
                print('data_db[data]')
                print(data_db['data'])
                df = pd.DataFrame(data_db['data'])
                print('df')
                print(df)
                df = df.tail(1)
                print('df tail')
                print(df)
                print('df last_seq')
                print(df['last_seq'])
                if df['last_seq'].values[0] == seq:
                    print("equal seq")
                else:
                    print("different seq")
                    data['num_seq'] = int(df['num_seq'].values[0]+1)
                    print('data')
                    print(data)
                    Database.push_doc("nodes", src, 'data', data)
            """ Create a current pdr database """
            print('data pdr')
            print(data)
            # Database.print_documents("pdr")
            # Calculate pdr rt->num_seqs * 100L / rt->last_seq;
            pdr = data['num_seq'] * 100.0 / data['last_seq']
            pdr_data = {
                '_id': src,
                'time': current_time,
                'pdr': pdr,
            }
            print('pdr')
            print(pdr)
            if Database.exist("pdr", src) == 0:
                Database.insert("pdr", pdr_data)
            else:
                print('updating pdr')
                Database.update_pdr("pdr", src, pdr_data)
            # print('printing pdr DB1')
            # Database.print_documents("pdr")
            """ after we finish updating the pdr field, we
            want to create/update pdr text so the canvas can
            be updated """
            coll = Database.find("pdr", {})
            df = pd.DataFrame(coll)
            print(df)
            mean = df.pdr.mean()
            print(mean)
            data = {
                "ts": current_time,
                "pdr": mean,
            }
            print('pdr data')
            print(data)
            """ Send to MQTT server/thingsboard """
            packet_topic = PDR.format(self.config.site)
            packet_message = json.dumps(data)
            self.mqtt.publish(packet_topic, packet_message)
            """ Save to DB """
            Database.insert("total_pdr", data)
            coll = Database.find("total_pdr", {})
            df = pd.DataFrame(coll)
            print(df)

    def process_neighbours(self, addr, payload_len, payload):
        print('processing neighbours from %s', addr)
        blocks = int(payload_len/6)
        print('range')
        print(range(1, blocks+1))
        for x in range(1, blocks+1):
            sliced_data = payload[(-1+x)*6:x*6]
            addr0, addr1, rssi, rank = struct.unpack('!bbhh', sliced_data)
            dst = str(addr1)+'.'+str(addr0)
            print('dest address %s', dst)
            data = {
                'time': current_time,
                'scr': addr,
                'dst': dst,
                'rssi': rssi,
                'rank': rank,
            }
            print('data')
            print(data)
            node = {
                '_id': addr,
                'nbr': [
                    data,
                ]
            }
            print('node')
            print(node)
            if Database.exist("nodes", addr) == 0:
                print('node does not exist, inserting...')
                Database.insert("nodes", node)
            else:
                print('node does exist, pushing...')
                Database.push_doc("nodes", addr, 'nbr', data)
            """ Insert entry to the links table """
            self.insert_links(data)
        # Database.print_documents("nodes")
        df = pd.DataFrame()
        coll = Database.find("nodes", {})
        for x in coll:
            print('x')
            print(x)
            if 'nbr' in x:
                df = pd.DataFrame(x['nbr'])
                print(df)

    def insert_links(self, data):
        links = {
            'time': data['time'],
            'scr': data['scr'],
            'dst': data['dst'],
            'rssi': data['rssi'],
        }
        print('inserting link')
        print(links)
        # load the collection to pandas frame
        db = Database.find_one("links", {})
        print('db links found?')
        print(db)
        if(db is None):
            print('no entries yet, inserting link')
            Database.insert("links", links)
        else:
            # It first checks if the links already exists in the collection.
            # If it does, it update with the current values, otherwise it creates it.
            Database.push_links("links", links)

    def process_nodes(self, addr, energy, rank, payload):
        # Calling DataFrame constructor on list
        # Database.print_documents("nodes")
        coll = Database.find("nodes", {})
        num_nb = 0
        for x in coll:
            if x['_id'] == addr:
                df = pd.DataFrame(x['nbr'])
                num_nb = df.dst.nunique()
                print(df)
        print('total nbrs')
        print(num_nb)
        data = {
            'time': current_time,
            'energy': energy,
            'rank': rank,
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
        # Database.print_documents("nodes")
        df = pd.DataFrame()
        # Calling DataFrame constructor on list
        coll = Database.find("nodes", {})
        for x in coll:
            if 'info' in x:
                df = pd.DataFrame(x['info'])
                print(df)
        """ Create a current energy database """
        # print('printing energy DB')
        # Database.print_documents("energy")
        print('creating energy DB')
        print('address:'+str(addr))
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
        # print('printing energy DB1')
        # Database.print_documents("energy")
        """ after we finish updating the energy field, we
        want to create/update energy text so the canvas can
        be updated """
        coll = Database.find("energy", {})
        df = pd.DataFrame(coll)
        print(df)
        summation = df.energy.sum()
        print(summation)
        data = {
            "ts": current_time,
            "energy": int(summation),
        }
        """ Send to MQTT server/thingsboard """
        packet_topic = ENERGY.format(self.config.site)
        packet_message = json.dumps(data)
        self.mqtt.publish(packet_topic, packet_message)
        """ Save to DB """
        Database.insert("total_energy", data)
        coll = Database.find("total_energy", {})
        df = pd.DataFrame(coll)
        print(df)

    def handle_serial(self, msg):
        global current_time
        # current_time = datetime.now()
        # Get Unix timestamp from a datetime object
        current_time = datetime.now().timestamp() * 1000.0

        msg.print_packet()
        # Save the packet in DB
        print('printing DB packet1')
        addr0 = str(msg.addr0)
        addr1 = str(msg.addr1)
        addr = addr0+'.'+addr1
        hex_data = bytes(msg.data).hex()
        print(hex_data)
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
        print('data')
        print(data)
        """ Send MQTT message """
        print('hello3')
        packet_topic = PACKET.format(self.config.site)
        print('hello4')
        print('data2')
        print(data)
        play_finished_message = json.dumps(data)
        print('play_finished_message')
        print(play_finished_message)
        print('hello5')
        self.mqtt.publish(packet_topic, play_finished_message)
        print('hello6')
        """ Save in DB """
        Database.insert("packets", data)
        # print('printing DB packet2')
        # Database.print_documents("packets")
        if(msg.message_type == 2):
            print("control packet")
            self.process_cp(msg)
        if(msg.message_type == 3):
            print("data packet received")
            self.process_data_packet(msg)

    def get_data(self):
        """This function serves the purpose of collecting data from the serial object and storing
        the filtered data into a global variable.
        The function has been put into a thread since the serial event is a blocking function.
        """
        msg = Message()
        while(1):
            try:
                msg = self.recv(0.1)
                if msg is not None:
                    print('msg')
                    print(msg.addr1)
                    print(msg)
                    self.handle_serial(msg)
            except TypeError:
                pass

    def send(self, msg, timeout=None):
        """
        Send a message over the serial device.
        """
        print('Sending message over the serial interface')
        byte_msg = bytearray()
        byte_msg.append(0x7E)
        self.check_byte(byte_msg, msg.addr0)
        self.check_byte(byte_msg, msg.addr1)
        self.check_byte(byte_msg, msg.message_type)
        self.check_byte(byte_msg, msg.payload_len)
        self.check_byte(byte_msg, msg.reserved0)
        self.check_byte(byte_msg, msg.reserved1)

        for i in range(0, msg.payload_len):
            # print('msg.data')
            # print(msg.data[i])
            self.check_byte(byte_msg, msg.data[i])
        byte_msg.append(0x7E)
        print('packet to send')
        print(byte_msg.hex())
        self.ser.send(byte_msg)

    def check_byte(self, byte_data, data):
        if (data == 0x7E or data == 0x7D):
            byte_data.append(0x7D)
            invert = data ^ (0x20)
            byte_data.append(invert)
        else:
            byte_data.append(data)

    def recv(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Block waiting for a message from the Bus.

        :param timeout:
            seconds to wait for a message or None to wait indefinitely

        :return:
            None on timeout or a :class:`Message` object.
        :raises can.CanError:
            if an error occurred while reading
        """
        start = time()
        time_left = timeout

        while True:

            # try to get a message
            # print('trying getting message')
            msg = self._recv_internal(timeout=time_left)

            if msg is not None:
                return msg

            # if not, and timeout is None, try indefinitely
            if timeout is None:
                print('timeout')
                continue

            # try next one only if there still is time, and with
            # reduced timeout
            else:

                time_left = timeout - (time() - start)

                if time_left > 0:
                    # print('time_left')
                    continue
                else:
                    # print('None')
                    return None

    def decodeByte(self, n):
        data = bytearray()
        scape_char = 0
        while len(data) < n:
            packet = self.ser.recv(n - len(data))
            if not packet:
                return None
            for byte in packet:
                if scape_char == 1:
                    # print('inverting')
                    scape_char = 0
                    int_packet = byte ^ (0x20)
                    byte = int_packet
                    # print(byte)
                    data.extend(bytes([byte]))
                elif byte == 0x7D:
                    # print('escape char found')
                    scape_char = 1
                    # n = n + 1
                else:
                    data.extend(bytes([byte]))
            # print('data')
            # print(data)
        return data

    def _recv_internal(self, timeout):
        """
        Read a message from the serial device.

        :param timeout:

            .. warning::
                This parameter will be ignored. The timeout value of the channel is used.

        :returns:
            Received message and False (because not filtering as taken place).

            .. warning::
                Flags like is_extended_id, is_remote_frame and is_error_frame
                will not be set over this function, the flags in the return
                message are the default values.

        :rtype:
            Tuple[can.Message, Bool]
        """
        try:
            # ser.read can return an empty string
            # or raise a SerialException
            rx_byte = self.ser.recv(1)
            # print("rx_byte")
            # print(rx_byte)
        except serial.SerialException:
            return None

        if rx_byte and ord(rx_byte) == 0x7E:
            print("start of frame found")
            addr0 = ord(self.decodeByte(1))
            print("addr0")
            print(addr0)
            addr1 = ord(self.decodeByte(1))
            print("addr1")
            print(addr1)
            message_type = ord(self.decodeByte(1))
            print("message_type")
            print(message_type)
            payload_len = ord(self.decodeByte(1))
            print("payload_len")
            print(payload_len)
            reserved0 = ord(self.decodeByte(1))
            print("reserved0")
            print(reserved0)
            reserved1 = ord(self.decodeByte(1))
            print("reserved1")
            print(reserved1)

            # if chunk == '':
            #     raise RuntimeError("socket connection broken")
            # chunks.append(chunk)

            data = self.decodeByte(payload_len)

            print('data')
            print(data.hex())

            rxd_byte = ord(self.ser.recv(1))
            if rxd_byte == 0x7E:
                print("correct frame")
                # received message data okay
                msg = Message(
                    addr0=addr0,
                    addr1=addr1,
                    message_type=message_type,
                    payload_len=payload_len,
                    reserved0=reserved0,
                    reserved1=reserved1,
                    data=data,
                )
                return msg

        else:
            return None
