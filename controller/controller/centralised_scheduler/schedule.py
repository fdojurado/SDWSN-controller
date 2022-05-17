from ast import Not
from pickletools import read_uint1
import types
import json
from controller.network_config.network_config import *

# Protocols encapsulated in sdn IP packet
cell_type = types.SimpleNamespace()
cell_type.UC_RX = 2
cell_type.UC_TX = 1


class Cell:
    def __init__(self, source=None, type=None, destination=None, channeloffset=None, timeoffset=None):
        self.source = source
        self.type = type
        self.destination = destination
        self.timeoffset = timeoffset
        self.channeloffset = channeloffset

    def __repr__(self):
        return "Cell(source={}, type={}, dest={}, timeoffset={}, channeloffset={})".format(
            self.source, self.type, self.destination, self.timeoffset, self.channeloffset)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


class Create_Node:
    def __init__(self, node):
        self.node = node
        self.rx = []
        self.tx = []

    def add_rx_cell(self, channeloffset, timeoffset):
        # print("adding rx cell")
        rx_cell = Cell(source=self.node, type=cell_type.UC_RX,
                       channeloffset=channeloffset, timeoffset=timeoffset)
        self.rx.append(rx_cell)
        return rx_cell

    def add_tx_cell(self, destination, timeoffset, channeloffset):
        # print("adding tx cell")
        # Cell duplicated?
        for tx_link in self.tx:
            if((tx_link.type == cell_type.UC_TX) and (tx_link.destination == destination)):
                # print("duplicated cell")
                return None

        tx_cell = Cell(source=self.node, type=cell_type.UC_TX, destination=destination,
                       timeoffset=timeoffset, channeloffset=channeloffset)

        self.tx.append(tx_cell)
        return tx_cell

    def is_link_in_cell(self, type, timeoffset, channeloffset, destination=None):
        if(type == cell_type.UC_RX):
            if not self.rx:
                for rx in self.rx:
                    if((timeoffset == rx.timeoffset) and (channeloffset == rx.channeloffset)):
                        return 1
        return 0

    def timeslot_empty(self, timeoffset):
        if not self.rx:
            for rx in self.rx:
                if(timeoffset == rx.timeoffset):
                    return 0
        if not self.tx:
            for tx in self.tx:
                if(timeoffset == tx.timeoffset):
                    return 0
        return 1

    def has_rx(self):
        if(not self.rx):
            return 0
        else:
            return 1

    def __repr__(self):
        return "Create_Node(Node={}, rx={}, tx={})".format(
            self.node, self.rx, self.tx)


class Schedule:
    def __init__(self, size, channel_offsets):
        self.slotframe_size = size
        self.num_channel_offsets = channel_offsets
        self.list_nodes = []
        self.clear_schedule()

    def add_uc(self, node, type, channeloffset=None, timeoffset=None, destination=None):
        # print("adding uc link node: ", node, " destination: ", destination, "type: ", type,
        #   " channeloffset: ", channeloffset, " timeoffset: ", timeoffset)
        if(not self.list_nodes):
            sensor = Create_Node(node)
            self.list_nodes.append(sensor)
            # print("creating new sensor")
        else:
            for elem in self.list_nodes:
                if (elem.node == node):
                    # print("sensor already exist")
                    sensor = elem
                    break
                else:
                    sensor = None
            if (sensor is None):
                sensor = Create_Node(node)
                self.list_nodes.append(sensor)
        # print("list of nodes: ", self.list_nodes)
        if(type == cell_type.UC_RX):
            # Check if the node already has a rx link
            if(not sensor.has_rx()):
                # print("adding rx uc at channeloffset ",
                #   channeloffset, " timeoffset ", timeoffset)
                rx_cell = sensor.add_rx_cell(channeloffset, timeoffset)
                self.schedule[channeloffset][timeoffset].append(rx_cell)
        if(type == cell_type.UC_TX and destination is not None):
            channeloffset, timeoffset = self.get_rx_coordinates(
                destination)
            if (channeloffset is not None and timeoffset is not None):
                # print("adding tx uc link from ", node, " to ", destination, " at channeloffset ",
                #   channeloffset, " timeoffset ", timeoffset)
                tx_cell = sensor.add_tx_cell(
                    destination, timeoffset, channeloffset)
                if(tx_cell is not None):
                    self.schedule[channeloffset][timeoffset].append(tx_cell)

        # self.print_schedule()

    def get_rx_coordinates(self, addr):
        # Get the time and channel offset from the given addr.
        for node in self.list_nodes:
            if node.rx:
                for rx in node.rx:
                    if (rx.source == str(addr)):
                        return rx.channeloffset, rx.timeoffset
        return None, None

    def clear_schedule(self):
        rows, cols = (self.num_channel_offsets, self.slotframe_size)
        self.schedule = [[0 for i in range(cols)] for j in range(rows)]
        for i in range(rows):
            for j in range(cols):
                self.schedule[i][j] = []
        self.list_nodes = []

    def format_printing_cell(self, cell):
        if(cell):
            # infr = "Node {fnode}, I'm {age}".format(fnode = cell.source, age = 36)
            match(cell.type):
                case cell_type.UC_RX:
                    info = "Rx ({fnode})".format(fnode=cell.source)
                    return info
                case cell_type.UC_TX:
                    info = "Tx ({fnode}-{dnode})".format(fnode=cell.source,
                                                         dnode=cell.destination)
                    return info
                case _:
                    print("unkown cell type")
                    return None

    def print_schedule(self):
        # print(*self.schedule, sep='\n')
        rows, cols = (self.num_channel_offsets, self.slotframe_size)
        print_schedule = [[0 for i in range(cols)] for j in range(rows)]
        for i in range(rows):
            for j in range(cols):
                print_schedule[i][j] = []
        for i in range(rows):
            for j in range(cols):
                if (self.schedule[i][j]):
                    for elem in self.schedule[i][j]:
                        txt = self.format_printing_cell(elem)
                        if(txt is not None):
                            print_schedule[i][j].append(txt)
        # print("printing schedule 2")
        print(*print_schedule, sep='\n')

    def schedule_toJSON(self, sf_len):
        # Build the schedule in a JSON format to be shared with the NC class
        # {
        #   "job_type": "TSCH",
        #   "sf_len": len
        #   "cells":[
        #               {
        #                   "addr": cell.source,
        #                   "channel": cell.channel,
        #                   "timeslot": cell.timeslot,
        #                   "type": cell.type,
        #                   "dest": cell.destination
        #                },
        #               {
        #                   "addr": cell.source,
        #                   "channel": cell.channel,
        #                   "timeslot": cell.timeslot,
        #                   "type": cell.type,
        #                   "dest": cell.destination
        #                },
        #       ]
        #   "hop_limit": "255"
        # }
        json_message_format = '{"job_type": ' + \
            str(job_type.TSCH)+', "cells":[]}'
        # parsing JSON string:
        json_message = json.loads(json_message_format)
        # hop_limit = 0
        rows, cols = (self.num_channel_offsets, self.slotframe_size)
        for i in range(rows):
            for j in range(cols):
                if (self.schedule[i][j]):
                    for elem in self.schedule[i][j]:
                        channel = str(elem.channeloffset)
                        timeslot = str(elem.timeoffset)
                        data = {"channel": channel, "timeslot": timeslot, "addr": elem.source, "type": elem.type,
                                "dest": elem.destination}
                        json_message["cells"].append(data)
                        # rank = get_rank(elem.source)
                        # if (rank > hop_limit):
                        #     hop_limit = rank
        json_message["hop_limit"] = 255
        json_message["sf_len"] = sf_len
        json_dump = json.dumps(json_message, indent=4, sort_keys=True)
        print(json_dump)
        return json_dump
