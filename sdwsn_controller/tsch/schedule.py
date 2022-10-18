import types
import json
from abc import ABC, abstractmethod
from rich.table import Table
from rich.console import Console
from rich.text import Text
import pandas as pd
import logging

# Protocols encapsulated in sdn IP packet
logger = logging.getLogger('main.'+__name__)
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
        logger.debug(f"Adding Rx cell at ch:{channeloffset}, ts:{timeoffset}")
        rx_cell = Cell(source=self.node, type=cell_type.UC_RX,
                       channeloffset=channeloffset, timeoffset=timeoffset)
        self.rx.append(rx_cell)
        return rx_cell

    def add_tx_cell(self, destination, timeoffset, channeloffset):
        logger.debug(f"Adding Tx cell for node destination {destination} at ch:{channeloffset}, ts:{timeoffset}")
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
    """ 
    Base class for TSCH schedules.

    Args:
        sf_size (int): The total maximum number of timeslots, this
        has to be long enough to support multiple slotframe sizes.
        channel_offsets (int): Maximum number of channels.
    """

    def __init__(self, sf_size, channel_offsets):
        self.__max_number_timeslots = sf_size
        self.__max_number_channels = channel_offsets
        self.__list_nodes = []
        self.schedule_clear_schedule()
        self.__sf_size = None

    @abstractmethod
    def run(self):
        pass

    def schedule_add_uc(self, node, type, channeloffset, timeoffset, destination=None):
        """ This adds a unicast link to the schedule. This does not do any verification
        on the status of the link to add. This has to be done by the scheduler.

        Args:
            node (str): This is the node to add the given type of link.
            type (cell_type): The type of link (Rx, Tx)
            channeloffset (int): The channel offset.
            timeoffset (int): The channel timeoffset.
            destination (str, optional): Destination node for Tx links. Defaults to None.
        """
        logger.debug(f"adding uc link to node: {node}, destination: {destination}, \
            type: {type} channeloffset: {channeloffset} timeoffset: {timeoffset}")
        if(not self.schedule_list_of_nodes):
            sensor = Node(node)
            self.schedule_list_of_nodes = sensor
            logger.debug("creating new sensor")
        else:
            for elem in self.schedule_list_of_nodes:
                if (elem.node == node):
                    logger.debug("sensor already exist")
                    sensor = elem
                    break
                else:
                    sensor = None
            if (sensor is None):
                sensor = Node(node)
                self.schedule_list_of_nodes = sensor
        if(type == cell_type.UC_RX):
            rx_cell = sensor.add_rx_cell(channeloffset, timeoffset)
            self.schedule_add_to_schedule(channeloffset, timeoffset, rx_cell)
        if(type == cell_type.UC_TX and destination is not None):
            tx_cell = sensor.add_tx_cell(
                destination, timeoffset, channeloffset)
            # if(tx_cell is not None):
            self.schedule_add_to_schedule(channeloffset, timeoffset, tx_cell)
        # self.print_schedule()

    @property
    def schedule_max_number_timeslots(self):
        return self.__max_number_timeslots

    @schedule_max_number_timeslots.setter
    def schedule_max_number_timeslots(self, val):
        self.__max_number_timeslots = val

    @property
    def schedule_max_number_channels(self):
        return self.__max_number_channels

    @schedule_max_number_channels.setter
    def schedule_max_number_channels(self, val):
        self.__max_number_channels = val

    @property
    def schedule_slot_frame_size(self):
        return self.__sf_size

    @schedule_slot_frame_size.setter
    def schedule_slot_frame_size(self, val):
        if val <= 0:
            raise Exception(f"Invalid slotframe size.")
        self.__sf_size = val

    @property
    def schedule_list_of_nodes(self):
        return self.__list_nodes

    @schedule_list_of_nodes.setter
    def schedule_list_of_nodes(self, val):
        self.__list_nodes.append(val)

    def schedule_get_schedule(self, ch_offset, ts_offset):
        if ch_offset > self.schedule_max_number_channels or ts_offset > self.schedule_max_number_timeslots:
            raise Exception(f"Invalid schedule coordinates.")
        return self.__schedule[ch_offset][ts_offset]

    def schedule_add_to_schedule(self, ch_offset, ts_offset, val):
        if ch_offset > self.schedule_max_number_channels or ts_offset > self.schedule_max_number_timeslots:
            raise Exception(f"Invalid schedule coordinates.")
        self.__schedule[ch_offset][ts_offset].append(val)

    def schedule_timeslot_free(self, ts):
        """
        This function checks whether the given timeslot is free

        Args:
            ts (int): Timeslot

        Returns:
            int: 1 if the timeslot is free; 0 otherwise.
        """
        for elem in self.schedule_list_of_nodes:
            for rx in elem.rx:
                if rx.timeoffset == ts:
                    return 0
            for tx in elem.tx:
                if tx.timeoffset == ts:
                    return 0
        return 1

    def schedule_is_node_timeslot_empty(self, node, timeslot):
        """
        It checks whether the timeslot of the given node
        is empty.

        Args:
            node (str): The sensor node address.
            timeslot (int): The timeslot.

        Returns:
            int: 1 if the timeslot is free; 0 otherwise.
        """
        for elem in self.schedule_list_of_nodes:
            if elem.node == node:
                return elem.timeslot_empty(timeslot)
        # If this is not found, then it is empty
        return 0

    def schedule_get_num_of_rx_cells(self, node):
        """
        Gets the total number of all Rx links

        Args:
            node (str): The sensor node address

        Returns:
            int: The total number of Rx links.
        """
        for elem in self.schedule_list_of_nodes:
            if elem.node == node:
                if elem.rx:
                    return len(elem.rx)
        return 0

    def schedule_get_rx_cells(self, node):
        """
        Gets all Rx links in the node

        Args:
            node (str): The sensor node address

        Returns:
            Node: The array of Rx cells.
        """
        #
        for elem in self.schedule_list_of_nodes:
            if elem.node == node:
                if elem.rx:
                    return elem.rx
        return None

    def schedule_link_exists(self, Tx, Rx):
        """
        It evaluates whether the given Tx-Rx links exists

        Args:
            Tx (str): Transmitter address.
            Rx (str): Received address.

        Returns:
            int: 1 if the link exists; 0 otherwise.
        """
        #
        for elem in self.schedule_list_of_nodes:
            if elem.node == Tx:
                for tx in elem.tx:
                    if tx.destination == Rx:
                        return 1
        return 0

    def schedule_get_rx_coordinates(self, addr):
        # Get the time and channel offset from the given addr.
        for node in self.schedule_list_of_nodes:
            if node.rx:
                for rx in node.rx:
                    if (rx.source == str(addr)):
                        return rx.channeloffset, rx.timeoffset
        return None, None

    def schedule_get_list_ts_in_use(self):
        """
        This function returns a list of timeslot currently used

        Returns:
            list: The list of the timeslot used.
        """
        #
        list_ts = []
        for ts in range(self.schedule_slot_frame_size):
            if not self.schedule_timeslot_free(ts):
                list_ts.append(ts)
        return list_ts

    def schedule_clear_schedule(self):
        """ 
        Clears the current schedule
        """
        rows, cols = (self.schedule_max_number_channels, self.schedule_max_number_timeslots)
        self.__schedule = [[0 for i in range(cols)] for j in range(rows)]
        for i in range(rows):
            for j in range(cols):
                self.__schedule[i][j] = []
        self.__list_nodes = []

    def schedule_format_printing_cell(self, cell):
        if(cell):
            # infr = "Node {fnode}, I'm {age}".format(fnode = cell.source, age = 36)
            match(cell.type):
                case cell_type.UC_RX:
                    info = "Rx ({fnode})".format(fnode=cell.source)
                    return info
                case cell_type.UC_TX:
                    info = "({fnode}-{dnode})".format(fnode=cell.source,
                                                      dnode=cell.destination)
                    return info
                case _:
                    logger.info("Unknown cell type")
                    return None

    def schedule_last_active_ts(self):
        """ 
        Last times offset of the current schedule

        Returns:
            int: Last active times offset.
        """
        last_ts = 0
        for node in self.schedule_list_of_nodes:
            for rx_cell in node.rx:
                if rx_cell.timeoffset > last_ts:
                    last_ts = rx_cell.timeoffset
            for tx_cell in node.tx:
                if tx_cell.timeoffset > last_ts:
                    last_ts = tx_cell.timeoffset

        return last_ts

    def schedule_last_active_channel(self):
        """ 
        Gets the last active channel of the current TSCH schedule

        Returns:
            int: last currently used channel
        """
        last_ch = 0
        for node in self.schedule_list_of_nodes:
            for rx_cell in node.rx:
                if rx_cell.channeloffset > last_ch:
                    last_ch = rx_cell.channeloffset
            for tx_cell in node.tx:
                if tx_cell.channeloffset > last_ch:
                    last_ch = tx_cell.channeloffset

        return last_ch

    def schedule_print(self):
        rows, cols = (self.schedule_max_number_channels, self.schedule_slot_frame_size)
        print_schedule = [[0 for i in range(cols)] for j in range(rows)]
        for i in range(rows):
            for j in range(cols):
                print_schedule[i][j] = []
        for i in range(rows):
            for j in range(cols):
                if (self.schedule_get_schedule(i, j)):
                    for elem in self.schedule_get_schedule(i, j):
                        txt = self.schedule_format_printing_cell(elem)
                        if(txt is not None):
                            print_schedule[i][j].append(txt)
        logger.info(*print_schedule, sep='\n')

    def schedule_print_table(self):
        """
        Prints a nice table using Rich library.
        """
        link_list = []
        for i in range(self.schedule_max_number_channels):
            for j in range(self.schedule_slot_frame_size):
                if (self.schedule_get_schedule(i, j)):
                    for cell in self.schedule_get_schedule(i, j):
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
        """
        This prints the TSCH schedules in a grid.
        """
        link_list = []
        for i in range(self.schedule_max_number_channels):
            for j in range(self.schedule_slot_frame_size):
                if (self.schedule_get_schedule(i, j)):
                    for cell in self.schedule_get_schedule(i, j):
                        txt = self.schedule_format_printing_cell(cell)
                        TSCH_cell_type = 'None'
                        match(cell.type):
                            case cell_type.UC_TX:
                                TSCH_cell_type = 'Transmitting'
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

        df.fillna('-', inplace=True)

        table = Table(
            title="TSCH schedules (Row -> Channels, Columns -> Timeoffsets)", show_lines=True)

        show_index = True

        index_name = ''

        if show_index:
            index_name = str(index_name) if index_name else ""
            table.add_column(index_name)

        for column in df.columns:
            table.add_column(str(column), justify="center")

        for index, value_list in enumerate(df.values.tolist()):
            row = [str(index)] if show_index else []
            row += [str(x) for x in value_list]
            table.add_row(*row)

        def log_table(rich_table):
            """Generate an ascii formatted presentation of a Rich table
            Eliminates any column styling
            """
            console = Console(width=150)
            with console.capture() as capture:
                console.print(rich_table)
            return Text.from_ansi(capture.get())

        logger.info(f"TSCH schedules table grid\n{log_table(table)}")
