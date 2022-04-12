from email.policy import strict
import struct
import types
import sys

# Packet sizes
SDN_IPH_LEN = 10  # Size of layer 3 packet header */
SDN_NDH_LEN = 6   # Size of neighbor discovery header */
SDN_NAH_LEN = 6   # Size of neighbor advertisment packet header */
SDN_NAPL_LEN = 6  # Size of neighbor advertisment payload size */
SDN_NCH_LEN = 6   # Size of network configuration routing and schedules packet header */
SDN_NCR_LEN = 4  # Size of NC routing packet*/
SDN_DATA_LEN = 8  # Size of data packet */
SDN_SERIAL_PACKETH_LEN = 6

# Protocols encapsulated in sdn IP packet
sdn_protocols = types.SimpleNamespace()
sdn_protocols.SDN_PROTO_ND = 1
sdn_protocols.SDN_PROTO_NA = 2              # Neighbor advertisement
sdn_protocols.SDN_PROTO_NC_ROUTE = 3        # Network configuration for routes
# Network configuration for schedules
sdn_protocols.SDN_PROTO_NC_SCHEDULES = 4
sdn_protocols.SDN_PROTO_DATA = 5            # Data packet


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
    else:
        result = sum
    return result


class addrConversion:
    def __init__(self, **kwargs):
        self.addr = kwargs.get("addr", 0)
        self.addrStr = kwargs.get("addrStr", "0.0")

    # optional: nice string representation of packet for printing purposes

    def __repr__(self):
        return "addrConversion(addr={}, addrStr={})".format(
            self.addr, self.addrStr)

    @classmethod
    def to_int(cls, addrStr):
        # Packs addrStr into two byte addr
        addrs = addrStr.split(".")
        payload = []
        for addr in addrs:
            if payload:
                pkt = struct.pack('!B'+str(len(payload)) +
                                  's', int(addr), bytes(payload))
            else:
                pkt = struct.pack('!B', int(addr))
            payload = pkt
        return cls(addr=pkt, addrStr=addrStr)

    @classmethod
    def to_string(cls, addr):
        addr_packed = struct.pack("!H", addr)
        addrStr = str(addr_packed[1])+"."+str(addr_packed[0])
        return cls(addr=addr, addrStr=addrStr)


class SerialPacket:

    def __init__(self, payload, **kwargs):
        self.addr = kwargs.get("addr", 0)
        self.message_type = kwargs.get("message_type", 0)
        self.payload_len = kwargs.get("payload_len", 0)
        self.reserved0 = kwargs.get("reserved0", 0)
        self.reserved1 = kwargs.get("reserved1", 0)
        self.payload = payload

    def pack(self):
        return struct.pack('!HBBBB' + str(len(self.payload)) + 's', self.addr, self.message_type,
                           self.payload_len, self.reserved0, self.reserved1, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "SerialPacket(addr={}, message_type={}, payload_len={}, reserved0={}, reserved1={}, payload={})".format(
            hex(self.addr), self.message_type, self.payload_len, self.reserved0, self.reserved1, self.payload)

    @classmethod
    def unpack(cls, packed_data):
        addr, message_type, payload_len, reserved0, reserved1, payload = struct.unpack(
            'HBBBB' + str(len(packed_data)-SDN_SERIAL_PACKETH_LEN) + 's', packed_data)
        return cls(payload, addr=addr, message_type=message_type, payload_len=payload_len,
                   reserved0=reserved0, reserved1=reserved1)


class SDN_IP_Packet:

    def __init__(self, payload, **kwargs):
        # One-byte long fields
        self.vap = kwargs.get("vap", 0)
        self.tlen = kwargs.get("tlen", 0)
        self.ttl = kwargs.get("ttl", 0)
        self.padding = kwargs.get("padding", 0)
        # These are two bytes long
        self.hdr_chksum = kwargs.get("hdr_chksum", 0)
        self.scr = kwargs.get("scr", 0)
        # Direct acces to addr in x.x format
        self.scrStr = kwargs.get("scrStr", "0.0")
        self.dest = kwargs.get("dest", 0)
        # Direct acces to addr in x.x format
        self.destStr = kwargs.get("destStr", "0.0")
        self.payload = payload

    def pack(self):
        #  Let's first compute the checksum
        data = struct.pack('!BBBBHHH', self.vap, self.tlen,
                           self.ttl, self.padding, self.hdr_chksum, self.scr, self.dest)
        self.hdr_chksum = sdn_ip_checksum(data, SDN_IPH_LEN)
        print("computed checksum")
        print(self.hdr_chksum)
        return struct.pack('!BBBBHHH' + str(len(self.payload)) + 's', self.vap, self.tlen,
                           self.ttl, self.padding, self.hdr_chksum, self.scr, self.dest, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "SDN_IP_Packet(vap={}, tlen={}, ttl={}, padding={}, hdr_chksum={}, scr={}, dest={}, payload={})".format(
            hex(self.vap), hex(self.tlen), hex(
                self.ttl), hex(self.padding), hex(self.hdr_chksum),
            hex(self.scr), hex(self.dest), self.payload)

    @classmethod
    def unpack(cls, packed_data):
        vap, tlen, ttl, padding, hdr_chksum, scr, dest, payload = struct.unpack(
            '!BBBBHHH' + str(len(packed_data)-SDN_IPH_LEN) + 's', packed_data)
        scrStr = addrConversion.to_string(scr)
        destStr = addrConversion.to_string(dest)
        return cls(payload, vap=vap, tlen=tlen, ttl=ttl, padding=padding, hdr_chksum=hdr_chksum,
                   scr=scr, scrStr=scrStr.addrStr, dest=dest, destStr=destStr.addrStr)


class NC_Routing_Packet:

    def __init__(self, payload, **kwargs):
        self.payload_len = kwargs.get("payload_len", 0)
        self.seq = kwargs.get("seq", 0)
        self.ack = kwargs.get("ack", 0)
        self.padding = kwargs.get("padding", 0)
        self.pkt_chksum = kwargs.get("pkt_chksum", 0)
        self.payload = payload

    def pack(self):
        #  Let's first compute the checksum
        data = struct.pack('!BBBBH' + str(len(self.payload)) + 's', self.payload_len, self.seq,
                           self.ack, self.padding, self.pkt_chksum, bytes(self.payload))
        self.pkt_chksum = sdn_ip_checksum(data, self.payload_len+SDN_NCH_LEN)
        print("computed checksum")
        print(self.pkt_chksum)
        return struct.pack('!BBBBH' + str(len(self.payload)) + 's', self.payload_len, self.seq,
                           self.ack, self.padding, self.pkt_chksum, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes

    def __repr__(self):
        return "NC_Routing_Packet(payload_len={}, seq={}, ack={}, pkt_chksum={}, payload={})".format(
            hex(self.payload_len), hex(self.seq),
            hex(self.ack), hex(self.pkt_chksum), self.payload)

    @classmethod
    def unpack(cls, packed_data, length):
        payload_len, seq, ack, padding, pkt_chksum, payload = struct.unpack(
            '!BBBBH' + str(length-SDN_NCH_LEN) + 's', packed_data)
        return cls(payload, payload_len=payload_len, seq=seq, ack=ack, padding=padding, pkt_chksum=pkt_chksum)


class NC_Routing_Payload:

    def __init__(self, payload, **kwargs):
        self.dst = kwargs.get("dst", 0)
        self.dst = addrConversion.to_int(self.dst).addr
        self.via = kwargs.get("via", 0)
        self.via = addrConversion.to_int(self.via).addr
        self.payload = payload

    def pack(self):
        if self.payload:
            packed = struct.pack('>2s2s'+str(len(self.payload)) +
                                 's', self.via, self.dst, bytes(self.payload))
        else:
            packed = struct.pack('!2s2s', self.via, self.dst)
        return packed

    # def pack(self, routes):
    #     # Let's loop into routes
    #     payload = []
    #     for index, route in self.routes.iterrows():
    #         dst = route['dst']
    #         via = route['via']
    #         dst = addrConversion.to_int(dst)
    #         via = addrConversion.to_int(via)
    #         if payload:
    #             pkt = struct.pack('>2s2s'+str(len(payload)) +
    #                               's', via.addr, dst.addr, bytes(payload))
    #         else:
    #             pkt = struct.pack('!2s2s', via.addr, dst.addr)
    #         payload = pkt

    #     return payload

    # optional: nice string representation of packet for printing purposes
    # def __repr__(self):
    #     output = ''
    #     for index, route in self.routes.iterrows():
    #         dst = route['dst']
    #         via = route['via']
    #         output = output + "NC_Routing_Packet(via={}, dest={})".format(
    #             via, dst)+"\n"
    #     return output


class DataPacketHeader:

    def __init__(self, payload, **kwargs):
        # One-byte long field
        self.length = kwargs.get("len", 0)
        self.payload = payload

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "DataPacketHeader(len={}, payload={})".format(
            self.length, self.payload)

    @classmethod
    def unpack(cls, packed_data):
        length, payload = struct.unpack(
            '!B' + str(len(packed_data)-SDN_DATAH_LEN) + 's', packed_data)
        return cls(payload, len=length)


class DataPacketPayload:

    def __init__(self, payload, **kwargs):
        # These are two bytes long
        self.addr = kwargs.get("addr", 0)
        # Direct acces to addr in x.x format
        self.addrStr = kwargs.get("addrStr", "0.0")
        self.seq = kwargs.get("seq", 0)
        self.temp = kwargs.get("temp", 0)
        self.humidity = kwargs.get("humidity", 0)
        self.payload = payload

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "DataPacketPayload(addr={}, seq={}, temp={}, humidity={}, payload={})".format(
            hex(self.addr), self.seq, self.temp, self.humidity, self.payload)

    @classmethod
    def unpack(cls, packed_data, payload_size):
        addr, seq, temp, humidity, payload = struct.unpack(
            '!HHHH' + str(payload_size) + 's', packed_data)
        addrStr = addrConversion.to_string(addr)
        return cls(payload, addr=addr, addrStr=addrStr.addrStr, seq=seq, temp=temp, humidity=humidity)


class NA_Packet:

    def __init__(self, payload, **kwargs):
        self.payload_len = kwargs.get("payload_len", 0)
        self.rank = kwargs.get("rank", 0)
        self.energy = kwargs.get("energy", 0)
        self.pkt_chksum = kwargs.get("pkt_chksum", 0)
        self.payload = payload

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "NA_Packet(payload_len={}, rank={}, energy={}, pkt_chksum={}, payload={})".format(
            hex(self.payload_len), hex(self.rank),
            hex(self.energy), hex(self.pkt_chksum), self.payload)

    @classmethod
    def unpack(cls, packed_data, length):
        payload_len, rank, energy, pkt_chksum, payload = struct.unpack(
            '!BBHH' + str(length-SDN_NAH_LEN) + 's', packed_data)
        return cls(payload, payload_len=payload_len, rank=rank, energy=energy, pkt_chksum=pkt_chksum)


class NA_Packet_Payload:

    def __init__(self, **kwargs):
        self.addr = kwargs.get("addr", 0)
        self.addrStr = kwargs.get("addrStr", "0.0")
        self.rssi = kwargs.get("rssi", 0)
        self.etx = kwargs.get("etx", 0)

    # optional: nice string representation of packet for printing purposes

    def __repr__(self):
        return "NA_Packet_Payload(addr={}, rssi={}, etx={})".format(
            self.addrStr, self.rssi, self.etx)

    @classmethod
    def unpack(cls, packed_data):
        addr, rssi, etx = struct.unpack(
            '!HhH', packed_data)
        addrStr = addrConversion.to_string(addr).addrStr
        return cls(addr=addr, addrStr=addrStr, rssi=rssi, etx=etx)
