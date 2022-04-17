from ast import Not
from pickletools import read_uint1


UC_RX = 0
UC_TX = 1


class Cell:
    def __init__(self, source=None, destination=None, channeloffset=None, timeoffset=None):
        self.source = source
        self.destination = destination
        self.timeoffset = timeoffset
        self.channeloffset = channeloffset


class Create_Node:
    def __init__(self, node):
        self.node = node
        self.rx = []
        self.tx = []

    def add_rx_cell(self, channeloffset, timeoffset):
        # print("adding rx cell")
        rx_cell = Cell(source=self.node, channeloffset=channeloffset, timeoffset=timeoffset,
                       )
        self.rx.append(rx_cell)
        # print(self.rx)

    def add_tx_cell(self, destination, timeoffset, channeloffset):
        # print("adding tx cell")
        tx_cell = Cell(source=self.node, destination=destination,
                       timeoffset=timeoffset, channeloffset=channeloffset)
        self.tx.append(tx_cell)
        # print(self.tx)

    def is_link_in_cell(self, type, timeoffset, channeloffset, destination=None):
        if(type == UC_RX):
            if not self.rx:
                for rx in self.rx:
                    if((timeoffset == rx.timeoffset) and (channeloffset == rx.channeloffset)):
                        return 1
        return 0

    def has_rx(self):
        if(not self.rx):
            return 0
        else:
            return 1


class Schedule:
    def __init__(self, size, channel_offsets):
        self.slotframe_size = size
        self.num_channel_offsets = channel_offsets
        self.list_nodes = []
        self.clear_schedule()

    def add_uc(self, node, type, channeloffset=None, timeoffset=None, destination=None):
        print("adding uc link node: ", node, " destination: ", destination, "type: ", type,
              " channeloffset: ", channeloffset, " timeoffset: ", timeoffset)
        if(not self.list_nodes):
            sensor = Create_Node(node)
            self.list_nodes.append(sensor)
        else:
            for elem in self.list_nodes:
                if (elem.node == node):
                    sensor = elem
                    break
                else:
                    sensor = Create_Node(node)
                    self.list_nodes.append(sensor)
                    break
        print("list of nodes: ", self.list_nodes)
        if(type == UC_RX):
            # Check if the node already has a rx link
            if(not sensor.has_rx()):
                print("adding rx uc at channeloffset ",
                      channeloffset, " timeoffset ", timeoffset)
                sensor.add_rx_cell(channeloffset, timeoffset)
                self.schedule[channeloffset][timeoffset].append(sensor)
        if(type == UC_TX and destination is not None):
            channeloffset, timeoffset = self.get_rx_coordinates(
                destination)
            if (channeloffset is not None and timeoffset is not None):
                print("adding tx uc link from ", node, " to ", destination, " at channeloffset ",
                      channeloffset, " timeoffset ", timeoffset)
                sensor.add_tx_cell(destination, timeoffset, channeloffset)
                self.schedule[channeloffset][timeoffset].append(sensor)

        self.print_schedule()

    def get_rx_coordinates(self, addr):
        # Get the time and channel offset from the given addr.
        for node in self.list_nodes:
            if node.rx:
                for rx in node.rx:
                    if (rx.source == addr):
                        return rx.channeloffset, rx.timeoffset
        return None, None

    def clear_schedule(self):
        rows, cols = (self.num_channel_offsets, self.slotframe_size)
        self.schedule = [[0 for i in range(cols)] for j in range(rows)]
        for i in range(rows):
            for j in range(cols):
                self.schedule[i][j] = []
        self.list_nodes = []

    def print_schedule(self):
        print(*self.schedule, sep='\n')