import random
from sdwsn_tsch.schedule import Schedule, cell_type


class HardCodedScheduler(Schedule):
    def __init__(
            self,
            sf_size: int = 500,
            channel_offsets: int = 3
    ):
        super().__init__(
            sf_size,
            channel_offsets)

    def run(self, path, current_sf_size):
        print(f"running hard coded scheduler for sf size {current_sf_size}")
        # Schedule Tx - Node 2 - 1
        tx_node = str(2)+".0"
        rx_node = str(1)+".0"
        ch = 1
        ts = 1
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Schedule Tx - Node 3 - 1
        tx_node = str(3)+".0"
        rx_node = str(1)+".0"
        ch = 1
        ts = 2
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Schedule Tx - Node 4 - 1
        tx_node = str(4)+".0"
        rx_node = str(1)+".0"
        ch = 1
        ts = 3
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Schedule Tx - Node 5 - 2
        tx_node = str(5)+".0"
        rx_node = str(2)+".0"
        ch = 1
        ts = 4
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Schedule Tx - Node 6 - 3
        tx_node = str(6)+".0"
        rx_node = str(3)+".0"
        ch = 1
        ts = 5
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Schedule Tx - Node 7 - 4
        tx_node = str(7)+".0"
        rx_node = str(4)+".0"
        ch = 1
        ts = 6
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Schedule Tx - Node 8 - 5
        tx_node = str(8)+".0"
        rx_node = str(5)+".0"
        ch = 1
        ts = 7
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Schedule Tx - Node 9 - 6
        tx_node = str(9)+".0"
        rx_node = str(6)+".0"
        ch = 1
        ts = 8
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)
        # Schedule Tx - Node 10 - 7
        tx_node = str(10)+".0"
        rx_node = str(7)+".0"
        ch = 1
        ts = 9
        self.schedule_add_uc(
            tx_node, cell_type.UC_TX, ch, ts, rx_node)
        self.schedule_add_uc(rx_node, cell_type.UC_RX, ch, ts)

        # Print the schedule
        self.schedule_print()
