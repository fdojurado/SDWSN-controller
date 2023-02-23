from sdwsn_controller.tsch.schedule import cell_type
import logging

logger = logging.getLogger('main.'+__name__)


class HardCodedScheduler():
    def __init__(
            self,
            sf_size: int = 500,
            channel_offsets: int = 3
    ):
        self.__name = "Hard Coded Scheduler"

    @property
    def name(self):
        return self.__name

    def add_link(self, network, tx_id, rx_id, ch, ts):
        tx_node = network.nodes_add(tx_id)
        rx_node = network.nodes_add(rx_id)
        tx_node.tsch_add_link(cell_type.UC_TX, ch, ts, rx_node.id)
        rx_node.tsch_add_link(cell_type.UC_RX, ch, ts)

    def run(self, path, current_sf_size, network):
        logger.debug(
            f"running hard coded scheduler for sf size {current_sf_size}")
        # Set the slotframe size
        network.tsch_clear()
        network.tsch_slotframe_size = current_sf_size
        # Schedule Tx - Node 2 - 1
        self.add_link(network, 2, 1, 1, 1)
        # Schedule Tx - Node 3 - 1
        self.add_link(network, 3, 1, 1, 2)
        # Schedule Tx - Node 4 - 1
        self.add_link(network, 4, 1, 1, 3)
        # Schedule Tx - Node 5 - 2
        self.add_link(network, 5, 2, 1, 4)
        # Schedule Tx - Node 6 - 3
        self.add_link(network, 6, 3, 1, 5)
        # Schedule Tx - Node 7 - 4
        self.add_link(network, 7, 4, 1, 6)
        # Schedule Tx - Node 8 - 5
        self.add_link(network, 8, 5, 1, 7)
        # Schedule Tx - Node 9 - 6
        self.add_link(network, 9, 6, 1, 8)
        # Schedule Tx - Node 10 - 7
        self.add_link(network, 10, 7, 1, 9)

        # Print the schedule
        network.tsch_print()
