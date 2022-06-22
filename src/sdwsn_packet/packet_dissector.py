# This class allows to read and write from the database
import struct
from sdwsn_packet.packet import serial_protocol, sdn_protocols
from sdwsn_packet.packet import SerialPacket, SDN_IP_Packet
from sdwsn_packet.packet import Data_Packet, NA_Packet, NA_Packet_Payload
from sdwsn_packet.packet import SDN_IPH_LEN, SDN_NAPL_LEN
from sdwsn_database.db_manager import DatabaseManager


class PacketDissector(DatabaseManager):
    def __init__(
            self,
            name: str = 'myDSN',
            host: str = '127.0.0.1',
            port: int = 27017,
            cycle_sequence: int = 0,
            sequence: int = 0
    ):
        super().__init__(name, host, port)
        self.ack_pkt = None
        self.cycle_sequence = cycle_sequence
        self.sequence = sequence

    def handle_serial_packet(self, data):
        # Let's parse serial packet
        serial_pkt = self.process_serial_packet(data)
        if serial_pkt is None:
            print("bad serial packet")
            return
        # Let's first save the packet
        self.save_serial_packet(serial_pkt.toJSON())
        # Check if this is a serial ACK packet
        if serial_pkt.message_type == serial_protocol.ACK:
            self.ack_pkt = serial_pkt
            return
        # Let's now process the sdn IP packet
        pkt = self.process_sdn_ip_packet(serial_pkt.payload)
        # We exit processing if empty result returned
        if(not pkt):
            return
        b = int.from_bytes(b'\x0F', 'big')
        protocol = pkt.vap & b
        match protocol:
            case sdn_protocols.SDN_PROTO_NA:
                # print("Processing NA packet")
                na_pkt = self.process_na_packet(pkt)
                if na_pkt is None:
                    print("bad NA packet")
                    return
                # Add to number of pkts received during this period
                if not na_pkt.cycle_seq == self.cycle_sequence:
                    return
                # print(repr(pkt))
                # print(repr(na_pkt))
                self.sequence += 1
                # print(f"num seq (NA): {self.sequence}")
                # We now build the energy DB
                self.save_energy(pkt, na_pkt)
                # We now build the neighbors DB
                self.save_neighbors(pkt, na_pkt)
                return
            case sdn_protocols.SDN_PROTO_DATA:
                # print("Processing data packet")
                data_pkt = self.process_data_packet(pkt)
                if data_pkt is None:
                    print("bad Data packet")
                    return
                # Add to number of pkts received during this period
                if not data_pkt.cycle_seq == self.cycle_sequence:
                    return
                # print(repr(pkt))
                # print(repr(data_pkt))
                self.sequence += 1
                # print(f"num seq (data): {self.sequence}")
                # We now build the pdr DB
                self.save_pdr(pkt, data_pkt)
                # We now build the delay DB
                self.save_delay(pkt, data_pkt)
                return
            case _:
                print("sdn IP packet type not found")
                return

    def process_serial_packet(self, data):
        # Parse sdn IP packet
        # print("processing serial packet")
        pkt = SerialPacket.unpack(data)
        # print(repr(pkt))
        # If the reported payload length in the serial header doesn't match the packet size,
        # then we drop the packet.
        if(len(pkt.payload) < pkt.payload_len):
            print("packet shorter than reported in serial header")
            return None
        # serial packet succeed
        # print("succeed unpacking serial packet")
        return pkt

    def process_data_packet(self, pkt):
        # If the reported length in the sdn IP header doesn't match the packet size,
        # then we drop the packet.
        if(len(pkt.payload) < (pkt.tlen-SDN_IPH_LEN)):
            print("Data packet shorter than reported in IP header")
            return
        # Process data packet header
        pkt = Data_Packet.unpack(pkt.payload)
        # print(repr(pkt))
        # sdn IP packet succeed
        # print("succeed unpacking sdn data packet")
        return pkt

    def process_sdn_ip_packet(self, data):
        # We first check the integrity of the HEADER of the sdn IP packet
        if(self.sdn_ip_checksum(data, SDN_IPH_LEN) != 0xffff):
            print("bad checksum")
            return
        # Parse sdn IP packet
        # print("processing IP packet")
        pkt = SDN_IP_Packet.unpack(data)
        # print(repr(pkt))
        # If the reported length in the sdn IP header doesn't match the packet size,
        # then we drop the packet.
        if(len(data) < pkt.tlen):
            print("packet shorter than reported in IP header")
            return
        # sdn IP packet succeed
        # print("succeed unpacking sdn IP packet")
        return pkt

    def chksum(self, sum, data, len):
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

    def sdn_ip_checksum(self, msg, len):
        sum = self.chksum(0, msg, len)
        result = 0
        if(sum == 0):
            result = 0xffff
            # print("return chksum ", result)
        else:
            result = struct.pack(">i", sum)
            # print("return chksum ", result)
        return result

    def process_na_packet(self, pkt):
        length = pkt.tlen-SDN_IPH_LEN
        # We first check the integrity of the entire SDN NA packet
        if(self.sdn_ip_checksum(pkt.payload, length) != 0xffff):
            print("bad NA checksum")
            return
        # Parse sdn NA packet
        pkt = NA_Packet.unpack(pkt.payload, length)
        # print(repr(pkt))
        # If the reported payload length in the sdn NA header does not match the packet size,
        # then we drop the packet.
        if(len(pkt.payload) < pkt.payload_len):
            print("NA packet shorter than reported in the header")
            return
        # sdn IP packet succeed
        # print("succeed unpacking SDN NA packet")
        return pkt
