import struct

# Header size of the control packet
CP_PKT_HEADER_SIZE = 10


class SerialControlPacket:

    def __init__(self, payload, **kwargs):
        self.addr0 = kwargs.get("addr0", 0)
        self.addr1 = kwargs.get("addr1", 0)
        self.message_type = kwargs.get("message_type", 0)
        self.payload_len = kwargs.get("payload_len", 0)
        self.reserved0 = kwargs.get("reserved0", 0)
        self.reserved1 = kwargs.get("reserved1", 0)
        self.payload = payload

    def pack(self):
        return struct.pack('!BBBBBB' + str(len(self.payload)) + 's', self.addr0, self.addr1, self.message_type, self.payload_len, self.reserved0, self.reserved1, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "SerialControlPacket(addr0={}, addr1={}, message_type={}, payload_len={}, reserved0={}, reserved1={}, payload={})".format(self.addr0, self.addr1, self.message_type, self.payload_len, self.reserved0, self.reserved1, self.payload)

    @classmethod
    def unpack(cls, packed_data):
        addr0, addr1, message_type, payload_len, reserved0, reserved1, payload = struct.unpack(
            'BBBBBB' + str(len(packed_data)-CP_PKT_HEADER_SIZE) + 's', packed_data)
        return cls(payload, addr0=addr0, addr1=addr1, message_type=message_type, payload_len=payload_len, reserved0=reserved0, reserved1=reserved1)
