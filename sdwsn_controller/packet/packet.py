#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import struct
import types
import json

# Packet sizes
SDN_IPH_LEN = 10  # Size of layer 3 packet header */
SDN_NDH_LEN = 6   # Size of neighbor discovery header */
SDN_NAH_LEN = 10   # Size of neighbor advertisement packet header */
SDN_NAPL_LEN = 6  # Size of neighbor advertisement payload size */
# SDN_NCH_LEN = 6   # Size of network configuration routing and schedules packet header */
SDN_RAH_LEN = 6  # Size of RA header routing packet*/
SDN_SAH_LEN = 6  # Size of SA header schedule packet*/
SDN_DATA_LEN = 11  # Size of data packet */
SDN_SERIAL_PACKETH_LEN = 8

# Message types for the serial interface
serial_protocol = types.SimpleNamespace()
serial_protocol.ACK = 4

# Protocols encapsulated in sdn IP packet
sdn_protocols = types.SimpleNamespace()
sdn_protocols.SDN_PROTO_ND = 1
sdn_protocols.SDN_PROTO_NA = 2        # Neighbor advertisement
sdn_protocols.SDN_PROTO_RA = 3        # Routes Advertisement
sdn_protocols.SDN_PROTO_SA = 4        # Schedule Advertisement
sdn_protocols.SDN_PROTO_DATA = 5      # Data packet


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
    if (sum == 0):
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

    # TODO: This methods' names are confusing.
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
        return cls(addr=addr_packed, addrStr=addrStr)


class SerialPacket:

    def __init__(self, payload, **kwargs):
        self.addr = kwargs.get("addr", 0)
        self.pkt_chksum = kwargs.get("pkt_chksum", 0)
        self.message_type = kwargs.get("message_type", 0)
        self.payload_len = kwargs.get("payload_len", 0)
        self.reserved0 = kwargs.get("reserved0", 0)
        self.reserved1 = kwargs.get("reserved1", 0)
        self.payload = payload

    def pack(self):
        #  Let's first compute the checksum
        data = struct.pack('!HHBBBB' + str(len(self.payload)) + 's', self.addr, self.pkt_chksum, self.message_type,
                           self.payload_len, self.reserved0, self.reserved1, bytes(self.payload))
        self.pkt_chksum = sdn_ip_checksum(
            data, self.payload_len+SDN_SERIAL_PACKETH_LEN)

        return struct.pack('!HHBBBB' + str(len(self.payload)) + 's', self.addr, self.pkt_chksum, self.message_type,
                           self.payload_len, self.reserved0, self.reserved1, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "SerialPacket(addr={}, pkt_chksum={}, message_type={}, \
        payload_len={}, reserved0={}, reserved1={}, payload={})".format(
            hex(self.addr), self.pkt_chksum, self.message_type,
            self.payload_len, self.reserved0, self.reserved1, self.payload)

    @classmethod
    def unpack(cls, packed_data):
        addr, pkt_chksum, message_type, payload_len, reserved0, reserved1, payload = struct.unpack(
            'HHBBBB' + str(len(packed_data)-SDN_SERIAL_PACKETH_LEN) + 's', packed_data)
        return cls(payload, addr=addr, pkt_chksum=pkt_chksum, message_type=message_type, payload_len=payload_len,
                   reserved0=reserved0, reserved1=reserved1)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__ if type(o) is not bytes else str(o),
                          sort_keys=True, indent=4)


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
        # Direct access to addr in x.x format
        self.scrStr = kwargs.get("scrStr", "0.0")
        self.dest = kwargs.get("dest", 0)
        # Direct access to addr in x.x format
        self.destStr = kwargs.get("destStr", "0.0")
        self.payload = payload

    def pack(self):
        #  Let's first compute the checksum
        data = struct.pack('!BBBBHHH', self.vap, self.tlen,
                           self.ttl, self.padding, self.hdr_chksum, self.scr, self.dest)
        self.hdr_chksum = sdn_ip_checksum(data, SDN_IPH_LEN)

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


class RA_Packet:

    def __init__(self, payload, **kwargs):
        self.payload_len = kwargs.get("payload_len", 0)
        self.padding = kwargs.get("padding", 0)
        self.seq = kwargs.get("seq", 0)
        self.pkt_chksum = kwargs.get("pkt_chksum", 0)
        self.payload = payload

    def pack(self):
        #  Let's first compute the checksum
        data = struct.pack('!BBHH' + str(len(self.payload)) + 's', self.payload_len,
                           self.padding, self.seq, self.pkt_chksum, bytes(self.payload))
        self.pkt_chksum = sdn_ip_checksum(data, self.payload_len+SDN_RAH_LEN)

        return struct.pack('!BBHH' + str(len(self.payload)) + 's', self.payload_len,
                           self.padding, self.seq, self.pkt_chksum, bytes(self.payload))

    # optional: nice string representation of packet for printing purposes

    def __repr__(self):
        return "RA_Packet(payload_len={}, seq={}, pkt_chksum={}, payload={})".format(
            hex(self.payload_len), self.seq, hex(self.pkt_chksum), self.payload)

    @classmethod
    def unpack(cls, packed_data, length):
        payload_len, seq, pkt_chksum, payload = struct.unpack(
            '!BBHH' + str(length-SDN_RAH_LEN) + 's', packed_data)
        return cls(payload, payload_len=payload_len, seq=seq, pkt_chksum=pkt_chksum)


class RA_Packet_Payload:

    def __init__(self, payload, **kwargs):
        self.src = kwargs.get("src", 0)
        self.src = addrConversion.to_int(self.src).addr
        self.dst = kwargs.get("dst", 0)
        self.dst = addrConversion.to_int(self.dst).addr
        self.via = kwargs.get("via", 0)
        self.via = addrConversion.to_int(self.via).addr
        self.payload = payload

    def pack(self):
        if self.payload:
            packed = struct.pack('>2s2s2s'+str(len(self.payload)) +
                                 's', self.src, self.dst, self.via, bytes(self.payload))
        else:
            packed = struct.pack('!2s2s2s', self.src, self.dst, self.via)
        return packed


class Cell_Packet:

    def __init__(self, payload, **kwargs):
        self.payload_len = kwargs.get("payload_len", 0)
        self.sf_len = kwargs.get("sf_len", 0)
        self.seq = kwargs.get("seq", 0)
        self.pkt_chksum = kwargs.get("pkt_chksum", 0)
        self.payload = payload

    def pack(self):
        #  Let's first compute the checksum
        data = struct.pack('!BBHH' + str(len(self.payload)) + 's', self.payload_len,
                           self.sf_len, self.seq, self.pkt_chksum, bytes(self.payload))
        self.pkt_chksum = sdn_ip_checksum(data, self.payload_len+SDN_SAH_LEN)

        return struct.pack('!BBHH' + str(len(self.payload)) + 's', self.payload_len,
                           self.sf_len, self.seq, self.pkt_chksum, bytes(self.payload))

    def __repr__(self):
        return "SA_Packet(payload_len={}, slotframe size={}, seq={}, pkt_chksum={}, payload={})".format(
            hex(self.payload_len), self.sf_len, self.seq, hex(self.pkt_chksum), self.payload)


class Cell_Packet_Payload:

    def __init__(self, payload, **kwargs):
        self.type = kwargs.get("type", 0)
        self.channel = kwargs.get("channel", 0)
        self.timeslot = kwargs.get("timeslot", 0)
        self.padding = kwargs.get("padding", 0)
        self.scr = kwargs.get("scr", 0)
        self.scr = addrConversion.to_string(self.scr).addr
        self.dst = kwargs.get("dst", 0)
        if self.dst is not None:
            self.dst = addrConversion.to_string(self.dst).addr
        else:
            self.dst = addrConversion.to_int('0.0').addr
        self.payload = payload

    def pack(self):
        if self.payload:
            packed = struct.pack('>bBBB2s2s'+str(len(self.payload)) +
                                 's', self.type, self.channel, self.timeslot,
                                 self.padding, self.scr, self.dst, bytes(self.payload))
        else:
            packed = struct.pack('!bBBB2s2s', self.type, self.channel,
                                 self.timeslot, self.padding, self.scr, self.dst)
        return packed


class Data_Packet:

    def __init__(self, **kwargs):
        self.cycle_seq = kwargs.get("cycle_seq", 0)
        self.seq = kwargs.get("seq", 0)
        self.temp = kwargs.get("temp", 0)
        self.humidity = kwargs.get("humidity", 0)
        self.light = kwargs.get("light", 0)
        self.asn_ls4b_lsb = kwargs.get("asn_ls4b_lsb", 0)
        self.asn_ls4b_msb = kwargs.get("asn_ls4b_msb", 0)
        self.asn_ms1b = kwargs.get("asn_ms1b", 0)
        self.asn_ls4b = (self.asn_ls4b_msb << 16) | (self.asn_ls4b_lsb)
        self.asn = (self.asn_ms1b << 32) | (self.asn_ls4b)

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "DataPacketPayload(cycle_seq={}, seq={}, temp={}, humidity={}, light={}, asn_ms1b={}, asn_ls4b={})".format(
            self.cycle_seq, self.seq, self.temp, self.humidity, self.light, self.asn_ms1b, self.asn_ls4b)

    @classmethod
    def unpack(cls, packed_data):
        cycle_seq, seq, temp, humidity, light, asn_ls4b_lsb, asn_ls4b_msb, asn_ms1b = struct.unpack(
            '!HBBBBHHB', packed_data)
        return cls(cycle_seq=cycle_seq, seq=seq, temp=temp, humidity=humidity,
                   light=light, asn_ls4b_lsb=asn_ls4b_lsb, asn_ls4b_msb=asn_ls4b_msb, asn_ms1b=asn_ms1b)


class NA_Packet:

    def __init__(self, payload, **kwargs):
        self.payload_len = kwargs.get("payload_len", 0)
        self.rank = kwargs.get("rank", 0)
        self.energy = kwargs.get("energy", 0)
        self.cycle_seq = kwargs.get("cycle_seq", 0)
        self.seq = kwargs.get("seq", 0)
        self.padding = kwargs.get("padding", 0)
        self.pkt_chksum = kwargs.get("pkt_chksum", 0)
        self.payload = payload

    # optional: nice string representation of packet for printing purposes
    def __repr__(self):
        return "NA_Packet(payload_len={}, rank={}, energy={}, cycle_seq={}, seq={}, pkt_chksum={}, payload={})".format(
            hex(self.payload_len), hex(self.rank), hex(self.energy),
            hex(self.cycle_seq), hex(self.seq), hex(self.pkt_chksum), self.payload)

    @classmethod
    def unpack(cls, packed_data, length):
        payload_len, rank, energy, cycle_seq, seq, _, pkt_chksum, payload = struct.unpack(
            '!BBHHBBH' + str(length-SDN_NAH_LEN) + 's', packed_data)
        return cls(payload, payload_len=payload_len, rank=rank, energy=energy,
                   cycle_seq=cycle_seq, seq=seq, pkt_chksum=pkt_chksum)


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
