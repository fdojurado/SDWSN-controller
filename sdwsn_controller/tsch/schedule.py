import types
import json
from abc import ABC, abstractmethod
from rich.table import Table
from rich.console import Console
from rich.text import Text
import pandas as pd
import logging

logger = logging.getLogger(__name__)
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


class Node:
    def __init__(self, node):
        self.node = node
        self.rx = []
        self.tx = []

    def add_rx_cell(self, channeloffset, timeoffset):
        # logger.info("adding rx cell")
        rx_cell = Cell(source=self.node, type=cell_type.UC_RX,
                       channeloffset=channeloffset, timeoffset=timeoffset)
        self.rx.append(rx_cell)
        return rx_cell

    def add_tx_cell(self, destination, timeoffset, channeloffset):
        # logger.info("adding tx cell")
        # Cell duplicated?
        # for tx_link in self.tx:
        #     if((tx_link.type == cell_type.UC_TX) and (tx_link.destination == destination)):
        #         # logger.info("duplicated cell")
        #         return None

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
        if self.rx:
            for rx in self.rx:
                if(timeoffset == rx.timeoffset):
                    return 0
        if self.tx:
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
        return "Node(Node={}, rx={}, tx={})".format(
            self.node, self.rx, self.tx)


class Schedule(ABC):
    def __init__(self, sf_size, channel_offsets):
        self.slotframe_size = sf_size
        self.num_channel_offsets = channel_offsets
        self.list_nodes = []
        # self.clear_schedule()

    @abstractmethod
    def run(self):
        pass

    def schedule_add_uc(self, node, type, channeloffset=None, timeoffset=None, destination=None):
        # logger.info("adding uc link node: ", node, " destination: ", destination, "type: ", type,
        #   " channeloffset: ", channeloffset, " timeoffset: ", timeoffset)
        if(not self.list_nodes):
            sensor = Node(node)
            self.list_nodes.append(sensor)
            # logger.info("creating new sensor")
        else:
            for elem in self.list_nodes:
                if (elem.node == node):
                    # logger.info("sensor already exist")
                    sensor = elem
                    break
                else:
                    sensor = None
            if (sensor is None):
                sensor = Node(node)
                self.list_nodes.append(sensor)
        # logger.info("list of nodes: ", self.list_nodes)
        if(type == cell_type.UC_RX):
            # Check if the node already has a rx link
            # if(not sensor.has_rx()):
            # logger.info("adding rx uc at channeloffset ",
            #   channeloffset, " timeoffset ", timeoffset)
            rx_cell = sensor.add_rx_cell(channeloffset, timeoffset)
            self.schedule[channeloffset][timeoffset].append(rx_cell)
        if(type == cell_type.UC_TX and destination is not None):
            # channeloffset, timeoffset = self.schedule_get_rx_coordinates(
            #     destination)
            # if (channeloffset is not None and timeoffset is not None):
            # logger.info("adding tx uc link from ", node, " to ", destination, " at channeloffset ",
            #   channeloffset, " timeoffset ", timeoffset)
            tx_cell = sensor.add_tx_cell(
                destination, timeoffset, channeloffset)
            if(tx_cell is not None):
                self.schedule[channeloffset][timeoffset].append(tx_cell)

        # self.print_schedule()

    def schedule_timeslot_free(self, ts):
        # This function checks whether the given timeslot is free
        # in the entire schedule
        for elem in self.list_nodes:
            for rx in elem.rx:
                if rx.timeoffset == ts:
                    return 0
            for tx in elem.tx:
                if tx.timeoffset == ts:
                    return 0
        return 1

    def schedule_is_timeslot_empty(self, node, timeslot):
        for elem in self.list_nodes:
            if elem.node == node:
                return elem.timeslot_empty(timeslot)
        # If this is not found, then it is empty
        return 1

    def schedule_get_num_of_cells(self, addr):
        # Get the total number of all Rx links
        for elem in self.list_nodes:
            if elem.node == addr:
                if elem.rx:
                    return len(elem.rx)
        return 0

    def schedule_get_rx_cells(self, addr):
        # Get all Rx links in the node
        for elem in self.list_nodes:
            if elem.node == addr:
                if elem.rx:
                    return elem.rx
        return None

    def schedule_link_exists(self, Tx, Rx):
        # It evaluates whether the given Tx-Rx links exists
        for elem in self.list_nodes:
            if elem.node == Tx:
                for tx in elem.tx:
                    if tx.destination == Rx:
                        return 1
        return 0

    def schedule_get_rx_coordinates(self, addr):
        # Get the time and channel offset from the given addr.
        for node in self.list_nodes:
            if node.rx:
                for rx in node.rx:
                    if (rx.source == str(addr)):
                        return rx.channeloffset, rx.timeoffset
        return None, None

    def schedule_get_list_ts_in_use(self):
        # This function returns a list of ts currently used
        list_ts = []
        for ts in range(self.slotframe_size):
            if not self.schedule_timeslot_free(ts):
                list_ts.append(ts)
        return list_ts

    def schedule_clear_schedule(self):
        rows, cols = (self.num_channel_offsets, self.slotframe_size)
        self.schedule = [[0 for i in range(cols)] for j in range(rows)]
        for i in range(rows):
            for j in range(cols):
                self.schedule[i][j] = []
        self.list_nodes = []

    def schedule_format_printing_cell(self, cell):
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
                    logger.info("Unknown cell type")
                    return None

    def schedule_last_active_ts(self):
        # Last timeslot offset of the current schedule
        last_ts = 0
        for node in self.list_nodes:
            for rx_cell in node.rx:
                if rx_cell.timeoffset > last_ts:
                    last_ts = rx_cell.timeoffset
            for tx_cell in node.tx:
                if tx_cell.timeoffset > last_ts:
                    last_ts = tx_cell.timeoffset

        return last_ts

    def schedule_last_active_channel(self):
        """Gets the last active channel of the current TSCH schedule
        TODO: This method is not tested.

        Returns:
            int: last currently used channel
        """
        last_ch = 0
        for node in self.list_nodes:
            for rx_cell in node.rx:
                if rx_cell.channeloffset > last_ch:
                    last_ch = rx_cell.channeloffset
            for tx_cell in node.tx:
                if tx_cell.channeloffset > last_ch:
                    last_ch = tx_cell.channeloffset

        return last_ch

    def schedule_set_sf_size(self, size):
        self.slotframe_size = size

    def schedule_print(self):
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
                        txt = self.schedule_format_printing_cell(elem)
                        if(txt is not None):
                            print_schedule[i][j].append(txt)
        # print("printing schedule 2")
        logger.info(*print_schedule, sep='\n')

    def schedule_print_table(self):
        link_list = []
        for i in range(self.num_channel_offsets):
            for j in range(self.slotframe_size):
                if (self.schedule[i][j]):
                    for cell in self.schedule[i][j]:
                        txt = self.schedule_format_printing_cell(cell)
                        TSCH_cell_type = 'None'
                        match(cell.type):
                            case cell_type.UC_RX:
                                TSCH_cell_type = 'Listening'
                            case cell_type.UC_TX:
                                TSCH_cell_type = 'Transmitting'
                            case _:
                                logger.info("Unknown cell type")
                        link_dict = {
                            'timeoffset': j,
                            'channeloffset': i,
                            'type': TSCH_cell_type,
                            'cell': txt
                        }
                        link_list.append(link_dict)

        # logger.info('TSCH schedules plain')
        # for elem in link_list:
        #     logger.info(elem)

        table = Table(title="TSCH schedules")

        table.add_column("Time offset", justify="center",
                         style="cyan", no_wrap=True)
        table.add_column("Channel offset", justify="center", style="magenta")
        table.add_column("Type", justify="left", style="green")
        table.add_column("Link \n(src, dst)", justify="left", style="blue")

        for elem in link_list:
            table.add_row(str(elem['timeoffset']), str(
                elem['channeloffset']), elem['type'], elem['cell'])

        def log_table(rich_table):
            """Generate an ascii formatted presentation of a Rich table
            Eliminates any column styling
            """
            console = Console(width=150)
            with console.capture() as capture:
                console.print(rich_table)
            return Text.from_ansi(capture.get())

        logger.info(f"TSCH schedules table\n{log_table(table)}")

    def schedule_print_grid(self):
        """This prints the TSCH schedules in a grid.
        TODO: This method is not tested.
        
        Returns:
            None
        """
        link_list = []
        for i in range(self.num_channel_offsets):
            for j in range(self.slotframe_size):
                if (self.schedule[i][j]):
                    for cell in self.schedule[i][j]:
                        txt = self.schedule_format_printing_cell(cell)
                        TSCH_cell_type = 'None'
                        match(cell.type):
                            case cell_type.UC_RX:
                                TSCH_cell_type = 'Listening'
                            case cell_type.UC_TX:
                                TSCH_cell_type = 'Transmitting'
                            case _:
                                logger.info("Unknown cell type")
                        link_dict = {
                            'timeoffset': j,
                            'channeloffset': i,
                            'type': TSCH_cell_type,
                            'cell': txt
                        }
                        link_list.append(link_dict)

        # Get the last active timeslot and channel
        max_columns = self.schedule_last_active_ts()
        max_rows = self.schedule_last_active_channel()

        # Create a pandas dataframe
        df = pd.DataFrame(index=range(0, max_rows+1),
                          columns=range(0, max_columns+1))

        for link in link_list:
            df.iloc[link['channeloffset'], link['timeoffset']] = link['cell']

        print(df.to_string())

