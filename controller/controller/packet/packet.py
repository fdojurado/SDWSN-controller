import struct

# Packet sizes
NC_ROUTING_PKT_SIZE = 4
# Header sizes
SERIAL_PKT_HEADER_SIZE = 6
CP_PKT_HEADER_SIZE = 10


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


class ControlPacket:

    def __init__(self, payload, **kwargs):
        # One-byte long field
        self.type = kwargs.get("type", 0)
        self.len = kwargs.get("len", 0)
        # These are two bytes long
        self.rank = kwargs.get("rank", 0)
        self.energy = kwargs.get("energy", 0)
        self.rt_chksum = kwargs.get("rt_chksum", 0)
        self.cpchksum = kwargs.get("cpchksum", 0)
        self.payload = payload

    def pack(self):
        return struct.pack('!BBHHHH' + str(len(self.payload)) + 's', self.type, self.len,
                           self.rank, self.energy, self.rt_chksum, self.cpchksum, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "ControlPacket(type={}, len={}, rank={}, energy={}, rt_chksum={}, cpchksum={}, payload={})".format(
            self.type, self.len, self.rank, self.energy, self.rt_chksum, self.cpchksum, self.payload)

    @classmethod
    def unpack(cls, packed_data):
        type, len, rank, energy, rt_chksum, cpchksum, payload = struct.unpack(
            'BBHHHH' + str(len(packed_data)-CP_PKT_HEADER_SIZE) + 's', packed_data)
        return cls(payload, type=type, len=len, rank=rank, energy=energy, rt_chksum=rt_chksum, cpchksum=cpchksum)


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
