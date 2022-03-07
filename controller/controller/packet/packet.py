import struct
import types

# Packet sizes
NC_ROUTING_PKT_SIZE = 4
DATA_PKT_PAYLOAD_SIZE = 8
NA_PKT_SIZE = 6
# Header sizes
SERIAL_PKT_HEADER_SIZE = 6
CP_PKT_HEADER_SIZE = 10
IP_PKT_HEADER_SIZE = 10
DATA_PKT_HEADER_SIZE = 1
# Protocols encapsulated in sdn IP packet
sdn_protocols = types.SimpleNamespace()
sdn_protocols.SDN_PROTO_ND = 1
sdn_protocols.SDN_PROTO_CP = 2
sdn_protocols.SDN_PROTO_NA = 3        # Neighbor advertisement
sdn_protocols.SDN_PROTO_PI = 4        # Packet-in
sdn_protocols.SDN_PROTO_PO = 5        # Packet-out
sdn_protocols.SDN_PROTO_NC = 6        # Network configuration
sdn_protocols.SDN_PROTO_NC_ACK = 7    # Neighbor advertisement
sdn_protocols.SDN_PROTO_DATA = 8      # Data packet


class SerialPacket:

    def __init__(self, payload, **kwargs):
        self.addr0 = kwargs.get("addr0", 0)
        self.addr1 = kwargs.get("addr1", 0)
        self.message_type = kwargs.get("message_type", 0)
        self.payload_len = kwargs.get("payload_len", 0)
        self.reserved0 = kwargs.get("reserved0", 0)
        self.reserved1 = kwargs.get("reserved1", 0)
        self.payload = payload

    def pack(self):
        return struct.pack('!BBBBBB' + str(len(self.payload)) + 's', self.addr0, self.addr1, self.message_type,
                           self.payload_len, self.reserved0, self.reserved1, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "SerialPacket(addr0={}, addr1={}, message_type={}, payload_len={}, reserved0={}, reserved1={}, payload={})".format(
            self.addr0, self.addr1, self.message_type, self.payload_len, self.reserved0, self.reserved1, self.payload)

    @classmethod
    def unpack(cls, packed_data):
        addr0, addr1, message_type, payload_len, reserved0, reserved1, payload = struct.unpack(
            'BBBBBB' + str(len(packed_data)-SERIAL_PKT_HEADER_SIZE) + 's', packed_data)
        return cls(payload, addr0=addr0, addr1=addr1, message_type=message_type, payload_len=payload_len,
                   reserved0=reserved0, reserved1=reserved1)


class SDN_IP_Packet:

    def __init__(self, payload, **kwargs):
        # One-byte long fields
        self.vahl = kwargs.get("vahl", 0)
        self.length = kwargs.get("len", 0)
        self.ttl = kwargs.get("ttl", 0)
        self.proto = kwargs.get("proto", 0)
        # These are two bytes long
        self.ipchksum = kwargs.get("ipchksum", 0)
        self.scr = kwargs.get("scr", 0)
        self.dest = kwargs.get("dest", 0)
        self.payload = payload

    def pack(self):
        return struct.pack('!BBBBHHH' + str(len(self.payload)) + 's', self.vahl, self.length,
                           self.ttl, self.proto, self.ipchksum, self.scr, self.dest, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "SDN_IP_Packet(vahl={}, len={}, ttl={}, proto={}, ipchksum={}, scr={}, dest={}, payload={})".format(
            hex(self.vahl), hex(self.length), hex(
                self.ttl), hex(self.proto), hex(self.ipchksum),
            hex(self.scr), hex(self.dest), self.payload)

    @classmethod
    def unpack(cls, packed_data):
        vahl, length, ttl, proto, ipchksum, scr, dest, payload = struct.unpack(
            '!BBBBHHH' + str(len(packed_data)-IP_PKT_HEADER_SIZE) + 's', packed_data)
        return cls(payload, vahl=vahl, len=length, ttl=ttl, proto=proto, ipchksum=ipchksum, scr=scr, dest=dest)


class ControlPacket:

    def __init__(self, payload, **kwargs):
        # One-byte long field
        self.type = kwargs.get("type", 0)
        self.length = kwargs.get("len", 0)
        # These are two bytes long
        self.rank = kwargs.get("rank", 0)
        self.energy = kwargs.get("energy", 0)
        self.rt_chksum = kwargs.get("rt_chksum", 0)
        self.cpchksum = kwargs.get("cpchksum", 0)
        self.payload = payload

    def pack(self):
        return struct.pack('!BBHHHH' + str(len(self.payload)) + 's', self.type, self.length,
                           self.rank, self.energy, self.rt_chksum, self.cpchksum, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "ControlPacket(type={}, len={}, rank={}, energy={}, rt_chksum={}, cpchksum={}, payload={})".format(
            self.type, self.length, self.rank, self.energy, self.rt_chksum, self.cpchksum, self.payload)

    @classmethod
    def unpack(cls, packed_data):
        type, length, rank, energy, rt_chksum, cpchksum, payload = struct.unpack(
            '!BBHHHH' + str(len(packed_data)-CP_PKT_HEADER_SIZE) + 's', packed_data)
        return cls(payload, type=type, len=length, rank=rank, energy=energy, rt_chksum=rt_chksum, cpchksum=cpchksum)


class NC_RoutingPacket:

    def __init__(self, routes, **kwargs):
        # These are two bytes long
        self.routes = routes

    def pack(self):
        # Let's loop into routes
        payload = []
        for index, route in self.routes.iterrows():
            dst = route['dst']
            via = route['via']
            if payload:
                pkt = struct.pack('>HH'+str(len(payload)) +
                                  's', int(float(via)), int(float(dst)), bytes(payload))
            else:
                pkt = struct.pack('!HH', int(float(via)), int(float(dst)))
            payload = pkt

        return payload

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        output = ''
        for index, route in self.routes.iterrows():
            dst = route['dst']
            via = route['via']
            output = output + "NC_RoutingPacket(via={}, dest={})".format(
                via, dst)+"\n"
        return output


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
            '!B' + str(len(packed_data)-DATA_PKT_HEADER_SIZE) + 's', packed_data)
        return cls(payload, len=length)


class DataPacketPayload:

    def __init__(self, payload, **kwargs):
        # These are two bytes long
        self.addr = kwargs.get("addr", 0)
        self.seq = kwargs.get("seq", 0)
        self.temp = kwargs.get("temp", 0)
        self.humidity = kwargs.get("humidity", 0)
        self.payload = payload

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "DataPacketPayload(addr={}, seq={}, temp={}, humidity={}, payload={})".format(
            self.addr, self.seq, self.temp, self.humidity, self.payload)

    @classmethod
    def unpack(cls, packed_data, payload_size):
        addr, seq, temp, humidity, payload = struct.unpack(
            '!HHHH' + str(payload_size) + 's', packed_data)
        return cls(payload, addr=addr, seq=seq, temp=temp, humidity=humidity)


class NA_Packet:

    def __init__(self, payload, **kwargs):
        # These are two bytes long
        self.addr = kwargs.get("addr", 0)
        self.rssi = kwargs.get("rssi", 0)
        self.rank = kwargs.get("rank", 0)
        self.payload = payload

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "NA_Packet(addr={}, rssi={}, rank={}, payload={})".format(
            self.addr, self.rssi, self.rank, self.payload)

    @classmethod
    def unpack(cls, packed_data, payload_size):
        addr, rssi, rank, payload = struct.unpack(
            '!HhH' + str(payload_size) + 's', packed_data)
        return cls(payload, addr=addr, rssi=rssi, rank=rank)
